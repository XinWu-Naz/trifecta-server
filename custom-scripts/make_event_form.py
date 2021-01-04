import pymongo
from pymongo import MongoClient
from datetime import datetime
import pytz
from bson.objectid import ObjectId
from bson.codec_options import CodecOptions
from random import choices
from dateutil import parser

client = MongoClient('localhost', 27017)
db = client.tritek

# data = {'owner': input("Owner: "), 'title': input("Title: "),
#         'venue': input("Venue: "), 
#         'datetime': datetime.now(pytz.utc),  # convert to utc
#         'attendees': []}

# lol = db.events.insert_one(data)
# print(lol)
frog = parser.parse("8:00 AM 29 Nov, 2020 GMT-8")
options = CodecOptions(tz_aware=True, tzinfo=pytz.timezone('Asia/Kuala_Lumpur'))
aware_times = db.events.with_options(codec_options=options)
f = aware_times.find_one({"_id": ObjectId("5fc29c76d61533caeac1c32f")}, {"attendees": 0})

print(f['datetime'])
print(frog.astimezone(pytz.utc))