import json

raw_data = '{"server": "Amazon", "config": {"port": 80, "active": true } }'
 
data = json.loads(raw_data)

print(data["config"]["port"])