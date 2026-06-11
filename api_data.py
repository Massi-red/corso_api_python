import json

raw_data = '{"server": "Amazon", "config": {"port": 80, "active": true } }'
 
data = json.loads(raw_data)

print(data["config"]["port"])

#json_social = '[{"id": 1, "tag": "python"}, {"id": 2, "tag": "gaming"}, {"id": 
#3, "tag": "python"}, {"id": 4, "tag": "webdev"}, {"id": 5, "tag": "python"}, {"id": 6, "tag": "gaming"}]'

#dude=json.loads(json_social)

#for p in dude:
#print(tag)
