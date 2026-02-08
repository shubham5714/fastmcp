import os
import sys
import io
import time
import socket
import uuid
import base64
import hashlib
import subprocess
import re
from datetime import datetime
from contextlib import contextmanager
from typing import Optional

import requests
import pychrome
import pytesseract
import modal

# Don't import FastAPI at the module level - import inside the function
# This allows modal serve to work without FastAPI installed locally


# Create Modal app and image
app = modal.App("rasterize")

# Create custom image with all dependencies
image = (
    modal.Image.debian_slim()
    .apt_install(
        # Browser
        "chromium",

        # Required runtime libs
        "fonts-liberation",
        "libnss3",
        "libxss1",
        "libasound2",
        "libatk-bridge2.0-0",
        "libgtk-3-0",
        "libdrm2",
        "libgbm1",

        # OCR
        "tesseract-ocr",

        # Utilities
        "ca-certificates",
        "wget",
    )
    .pip_install(
        "pychrome",
        "pillow",
        "pytesseract",
        "psutil",
        "fastapi[standard]"
    )
)


# Chrome management functions
def get_free_port():
    """Get a free port assigned by the OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))  # Port 0 tells OS to assign any free port
        s.listen(1)
        port = s.getsockname()[1]
    return port

def start_chrome():
    chrome_path = "chromium"
    
    print(f"\nStarting Chrome instance...")
    
    max_retries = 3
    process = None
    
    for attempt in range(max_retries):
        # Get a NEW free port for each attempt
        port = get_free_port()
        
        chrome_cmd = [
            chrome_path,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={port}"
        ]
        
        print(f"Attempt {attempt + 1}: Using port {port}")
        
        try:
            process = subprocess.Popen(
                chrome_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Wait for Chrome to start and port to be available
            for i in range(10):  # Try for 10 seconds
                try:
                    requests.get(f"http://127.0.0.1:{port}", timeout=1)
                    print(f"Chrome successfully started on port {port}! (PID: {process.pid})")
                    return process, port
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    continue
                
            raise Exception(f"Chrome started but debugging port {port} is not responding")
            
        except Exception as e:
            print(f"Failed to start Chrome on attempt {attempt + 1}: {e}")
            if process:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    pass
            if attempt == max_retries - 1:
                raise Exception(f"Failed to start Chrome after {max_retries} attempts: {e}")
            time.sleep(2)
            
    return None, None

def terminate_chrome(process):
    """Gracefully terminate Chrome process."""
    if process:
        try:
            process.terminate()
            try:
                process.wait(timeout=5)
                print("Chrome process terminated gracefully")
            except subprocess.TimeoutExpired:
                print("Chrome didn't terminate in time, forcing kill...")
                process.kill()
                process.wait(timeout=2)
                print("Chrome process killed")
        except Exception as e:
            print(f"Error terminating Chrome: {e}")
            try:
                process.kill()
            except Exception as kill_error:
                print(f"Error force killing Chrome: {kill_error}")

def cleanup_tab_and_browser(tab, browser):
    """Properly cleanup tab and browser to avoid WebSocket errors."""
    @contextmanager
    def suppress_all_output():
        """Suppress both stdout and stderr."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    with suppress_all_output():
        # Stop the tab first (stops WebSocket communication)
        if tab:
            try:
                tab.stop()
            except:
                pass
        
        # Small delay to ensure WebSocket is closed
        time.sleep(0.5)
        
        # Close the tab
        if tab and browser:
            try:
                browser.close_tab(tab)
            except:
                pass

def generate_run_id():
    """Generate a unique ID for each run combining timestamp and random string."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_str = str(uuid.uuid4())[:8]
    return f"{timestamp}_{random_str}"

def get_tesseract_path():
    """Get the appropriate tesseract path based on the environment."""
    possible_paths = ['tesseract']
    
    for path in possible_paths:
        try:
            if path == 'tesseract':
                subprocess.run(['tesseract', '--version'], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE,
                             check=True)
                print(f"Found tesseract in system PATH")
                return path
            elif os.path.exists(path):
                print(f"Found tesseract at: {path}")
                return path
        except Exception:
            continue
    
    raise Exception("Tesseract not found in common locations. Please ensure it is installed correctly.")

def validate_ocr_text(text):
    """
    Validate OCR text using regex patterns and extract detection score.
    Returns a dictionary with score and status.
    """
    # Pattern 1: Detection count format (e.g., "3/97 security", "10/95 security", etc.)
    pattern1 = r'(\d?\d)/\d\d\s+security'
    
    # Pattern 2: No security vendors detected
    pattern2 = r'No\s+security\s+vendor'
    
    # Pattern 3: At least X detected
    pattern3 = r'least\s+(\d+)\s+detected'
    
    # Try pattern 1 first - extract the detection number
    match1 = re.search(pattern1, text, re.IGNORECASE)
    if match1:
        score = match1.group(1)  # Extract the first number (detections)
        print(f"Reputation Score Found - Score: {score}")
        return {
            "score": score,
            "status": "success",
            "raw_text": text
        }
    
    # Try pattern 2 if pattern 1 fails
    match2 = re.search(pattern2, text, re.IGNORECASE)
    if match2:
        print(f"Pattern 2 matched - No security vendors flagged")
        return {
            "score": "0",
            "status": "success",
            "raw_text": text
        }
    
    # Try pattern 3 if pattern 2 fails
    match3 = re.search(pattern3, text, re.IGNORECASE)
    if match3:
        print(f"Pattern 3 matched - Domain is legit")
        return {
            "score": "0",
            "status": "success",
            "raw_text": text
        }
    
    # All patterns failed
    print(f"All regex patterns failed to match")
    return {
        "score": "0",
        "status": "error",
        "raw_text": text
    }

def get_hash_intel(hash):
    run_id = generate_run_id()
    chrome_process = None
    browser = None
    tab = None
    
    try:
        chrome_process, port = start_chrome()
        if not chrome_process:
            raise Exception("Failed to start Chrome")

        pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()
        browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
        tab = browser.new_tab()

        tab.start()
        tab.call_method("Page.enable")
        tab.call_method("DOM.enable")

        tab.call_method("Emulation.setDeviceMetricsOverride",
            width=1024,
            height=1024,
            deviceScaleFactor=1,
            mobile=False,
            screenOrientation={"angle": 0, "type": "portraitPrimary"}
        )

        screenshot_filename = f"hash_intel_{run_id}.png"
        screenshot_path = f"screenshots/{screenshot_filename}"
        os.makedirs("screenshots", exist_ok=True)

        target_url = f"https://www.virustotal.com/gui/file/{hash}/details"
        tab.call_method("Page.navigate", url=target_url)
        tab.wait(10)

        screenshot = tab.call_method("Page.captureScreenshot", format="png", fromSurface=True)

        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))
            f.flush()
            os.fsync(f.fileno())

        if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
            raise Exception("Screenshot file was not properly saved")

        text = pytesseract.image_to_string(screenshot_path, lang='eng')
       
        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            print(f"Error cleaning up screenshot: {e}")

        # Validate OCR text before returning
        return validate_ocr_text(text)
        
    finally:
        cleanup_tab_and_browser(tab, browser)
        if chrome_process:
            terminate_chrome(chrome_process)

def get_ip_intel(ip):
    run_id = generate_run_id()
    chrome_process = None
    browser = None
    tab = None
    
    try:
        chrome_process, port = start_chrome()
        if not chrome_process:
            raise Exception("Failed to start Chrome")

        pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()
        browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
        tab = browser.new_tab()

        tab.start()
        tab.call_method("Page.enable")
        tab.call_method("DOM.enable")

        tab.call_method("Emulation.setDeviceMetricsOverride",
            width=1024,
            height=800,
            deviceScaleFactor=1,
            mobile=False,
            screenOrientation={"angle": 0, "type": "portraitPrimary"}
        )

        screenshot_filename = f"ip_intel_{run_id}.png"
        screenshot_path = f"screenshots/{screenshot_filename}"
        os.makedirs("screenshots", exist_ok=True)

        target_url = f"https://www.virustotal.com/gui/ip-address/{ip}/details"
        tab.call_method("Page.navigate", url=target_url)
        tab.wait(10)
        
        screenshot = tab.call_method("Page.captureScreenshot", format="png", fromSurface=True)
        
        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))
            f.flush()
            os.fsync(f.fileno())

        if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
            raise Exception("Screenshot file was not properly saved")
        
        text = pytesseract.image_to_string(screenshot_path, lang='eng')

        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            print(f"Error cleaning up screenshot: {e}")

        # Validate OCR text before returning
        return validate_ocr_text(text)
        
    finally:
        cleanup_tab_and_browser(tab, browser)
        if chrome_process:
            terminate_chrome(chrome_process)

def get_domain_intel(domain):
    run_id = generate_run_id()
    chrome_process = None
    browser = None
    tab = None
    
    try:
        chrome_process, port = start_chrome()
        if not chrome_process:
            raise Exception("Failed to start Chrome")

        pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()
        browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
        tab = browser.new_tab()

        tab.start()
        tab.call_method("Page.enable")
        tab.call_method("DOM.enable")

        tab.call_method("Emulation.setDeviceMetricsOverride",
            width=1024,
            height=1024,
            deviceScaleFactor=1,
            mobile=False,
            screenOrientation={"angle": 0, "type": "portraitPrimary"}
        )

        screenshot_filename = f"domain_intel_{run_id}.png"
        screenshot_path = f"screenshots/{screenshot_filename}"
        os.makedirs("screenshots", exist_ok=True)

        target_url = f"https://www.virustotal.com/gui/domain/{domain}/details"
        tab.call_method("Page.navigate", url=target_url)
        tab.wait(10)

        screenshot = tab.call_method("Page.captureScreenshot", format="png", fromSurface=True)

        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))
            f.flush()
            os.fsync(f.fileno())

        if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
            raise Exception("Screenshot file was not properly saved")

        text = pytesseract.image_to_string(screenshot_path, lang='eng')
       
        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            print(f"Error cleaning up screenshot: {e}")

        # Validate OCR text before returning
        return validate_ocr_text(text)
        
    finally:
        cleanup_tab_and_browser(tab, browser)
        if chrome_process:
            terminate_chrome(chrome_process)

def get_url_intel(url):
    """Get intelligence for a URL by converting it to SHA256 hash and querying VirusTotal."""
    run_id = generate_run_id()
    chrome_process = None
    browser = None
    tab = None
    
    # Convert URL to SHA256 hash BEFORE try block so it always prints
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    print(f"\n{'='*60}")
    print(f"URL Intel Request")
    print(f"{'='*60}")
    print(f"Input URL: {url}")
    print(f"SHA256 Hash: {url_hash}")
    print(f"{'='*60}\n")
    
    try:
        
        chrome_process, port = start_chrome()
        if not chrome_process:
            raise Exception("Failed to start Chrome")

        pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()
        browser = pychrome.Browser(url=f"http://127.0.0.1:{port}")
        tab = browser.new_tab()

        tab.start()
        tab.call_method("Page.enable")
        tab.call_method("DOM.enable")

        tab.call_method("Emulation.setDeviceMetricsOverride",
            width=1024,
            height=1024,
            deviceScaleFactor=1,
            mobile=False,
            screenOrientation={"angle": 0, "type": "portraitPrimary"}
        )

        screenshot_filename = f"url_intel_{run_id}.png"
        screenshot_path = f"screenshots/{screenshot_filename}"
        os.makedirs("screenshots", exist_ok=True)

        target_url = f"https://www.virustotal.com/gui/url/{url_hash}/details"
        tab.call_method("Page.navigate", url=target_url)
        tab.wait(10)

        screenshot = tab.call_method("Page.captureScreenshot", format="png", fromSurface=True)

        with open(screenshot_path, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))
            f.flush()
            os.fsync(f.fileno())

        if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
            raise Exception("Screenshot file was not properly saved")

        text = pytesseract.image_to_string(screenshot_path, lang='eng')
       
        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as e:
            print(f"Error cleaning up screenshot: {e}")

        # Validate OCR text before returning
        return validate_ocr_text(text)
        
    finally:
        cleanup_tab_and_browser(tab, browser)
        if chrome_process:
            terminate_chrome(chrome_process)


# Authentication helper
def verify_api_key(request):
    """Verify the API key from the Authorization header."""
    from fastapi import HTTPException
    
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # Expected format: "Bearer <api_key>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401, 
            detail="Invalid Authorization header format. Use: Bearer <api_key>"
        )
    
    provided_key = parts[1]
    
    # Get the API key from environment variable (set via Modal secrets)
    expected_key = os.environ.get("API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    
    if provided_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return True


# Create the FastAPI web endpoint
@app.function(
    image=image,
    timeout=300,
    secrets=[modal.Secret.from_name("rasterize-auth")],
    max_containers=10
)
@modal.asgi_app()
@modal.concurrent(max_inputs=10)
def fastapi_app():
    from fastapi import FastAPI, Request
    from pydantic import BaseModel
    
    # Define Pydantic models inside the function
    class HashIntelRequestModel(BaseModel):
        hash: str

    class IPIntelRequestModel(BaseModel):
        ip: str

    class DomainIntelRequestModel(BaseModel):
        domain: str

    class URLIntelRequestModel(BaseModel):
        url: str

    class IntelResponseModel(BaseModel):
        success: bool
        score: Optional[str] = None
        status: Optional[str] = None
        data: Optional[str] = None
        error: Optional[str] = None
    
    web_app = FastAPI(
        title="Rasterize Intelligence API",
        description="API for gathering intelligence from VirusTotal via web scraping and OCR",
        version="1.0.0"
    )
    
    @web_app.get("/")
    def root():
        return {
            "message": "Rasterize Intelligence API",
            "endpoints": {
                "/hash": "POST - Get intelligence for a file hash",
                "/ip": "POST - Get intelligence for an IP address",
                "/domain": "POST - Get intelligence for a domain",
                "/url": "POST - Get intelligence for a URL (converted to SHA256)"
            },
            "authentication": "Required - Use 'Authorization: Bearer <api_key>' header"
        }
    
    @web_app.post("/hash", response_model=IntelResponseModel)
    def hash_intel_endpoint(request_body: HashIntelRequestModel, request: Request):
        """Get intelligence for a file hash from VirusTotal."""
        verify_api_key(request)
        try:
            result = get_hash_intel(request_body.hash)
            return IntelResponseModel(
                success=True,
                score=result["score"],
                status=result["status"]
            )
        except Exception as e:
            return IntelResponseModel(success=False, score="0", status="error", error=str(e))
    
    @web_app.post("/ip", response_model=IntelResponseModel)
    def ip_intel_endpoint(request_body: IPIntelRequestModel, request: Request):
        """Get intelligence for an IP address from VirusTotal."""
        verify_api_key(request)
        try:
            result = get_ip_intel(request_body.ip)
            return IntelResponseModel(
                success=True,
                score=result["score"],
                status=result["status"]
            )
        except Exception as e:
            return IntelResponseModel(success=False, score="0", status="error", error=str(e))
    
    @web_app.post("/domain", response_model=IntelResponseModel)
    def domain_intel_endpoint(request_body: DomainIntelRequestModel, request: Request):
        """Get intelligence for a domain from VirusTotal."""
        verify_api_key(request)
        try:
            result = get_domain_intel(request_body.domain)
            return IntelResponseModel(
                success=True,
                score=result["score"],
                status=result["status"]
            )
        except Exception as e:
            return IntelResponseModel(success=False, score="0", status="error", error=str(e))
    
    @web_app.post("/url", response_model=IntelResponseModel)
    def url_intel_endpoint(request_body: URLIntelRequestModel, request: Request):
        """Get intelligence for a URL from VirusTotal (URL is converted to SHA256)."""
        verify_api_key(request)
        try:
            result = get_url_intel(request_body.url)
            return IntelResponseModel(
                success=True,
                score=result["score"],
                status=result["status"]
            )
        except Exception as e:
            return IntelResponseModel(success=False, score="0", status="error", error=str(e))
    
    return web_app