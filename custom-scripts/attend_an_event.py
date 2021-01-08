from bson.json_util import dumps
import requests

key_api = input("key_api: ")
event_id = input("event_id: ")

r = requests.post("http://localhost:6969/attend_event", data=dumps({"key_api": key_api, "event_id": event_id}))
print(r.json())