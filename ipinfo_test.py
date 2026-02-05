import ipinfo

# Initialize Lite handler
handler = ipinfo.getHandlerLite(access_token='5b3e1d46453882')

# Look up a specific IP address
details = handler.getDetails("8.8.8.8")

print(details.ip)              # '8.8.8.8'
print(details.country_code)    # 'US'
print(details.country)         # 'United States'
print(details.asn)             # 'AS15169'
print(details.as_name)         # 'Google LLC'

print(details.all)
