#!/usr/bin/env python

import time
import random
import json
# aptitude install python-requests
import requests

url = "http://localhost:8080/api/network/ping"
data = { 'host': 'google.com', 'times' : [random.randint(20,90), random.randint(20,90), random.randint(20,90)], 'timestamp' : int(time.time())}
headers = {'Content-type': 'application/json', 'Accept': 'application/vnd.sensor.jauu.net.v1+json'}
r = requests.post(url, data=json.dumps(data), headers=headers)
print("Status Code:")
print(r.status_code)
print("")
print("URL:")
print(r.url)
print("")
print("Encoding:")
print(r.encoding)
print("")
print("Content:")
print(r.content)
print("")
#print("Json")
#print(r.json())
