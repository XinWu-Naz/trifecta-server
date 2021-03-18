from flask import Flask, request, redirect
from flask_pymongo import PyMongo
import pymongo

from bson.objectid import ObjectId
from bson.json_util import loads, dumps, RELAXED_JSON_OPTIONS
from passlib.hash import sha256_crypt
from random import SystemRandom
from datetime import datetime
from dateutil import parser
from pymongo.collection import ReturnDocument
import json
import pytz

import helper

"""
little note about time, store time in utc, show them back to me in my local time.
datetime.now(pytz.utc).astimezone()
with datetime.now(pytz.utc) it will give you utc time and tzinfo that tell its utc
by adding .astimezone() at the end, it will show it to us in local time!!

>>> from datetime import datetime
>>> import pytz  
>>> datetime.now(pytz.utc) 
datetime.datetime(2020, 11, 28, 11, 52, 4, 170629, tzinfo=<UTC>)
>>> datetime.now(pytz.utc).astimezone()
datetime.datetime(2020, 11, 28, 19, 52, 7, 986749, tzinfo=datetime.timezone(datetime.timedelta(seconds=28800), 'Malay Peninsula Standard Time'))
>>>
"""


app = Flask(__name__)
app.config[
    "MONGO_URI"
] = "mongodb://the_mongodb:27017/trifecta"

# with open('SECRET_SECRET', mode='rb') as f:
#     SECRET_KEY = f.read()

# app.secret_key = SECRET_KEY
crypto = SystemRandom()
mongo = PyMongo(app)

# my_printer = pprint.PrettyPrinter(depth=2)
success = "success"


@app.route("/")
def main():
    return {"message": "hi"}


############################## Account ############################
@app.route("/register", methods=["POST"])
def register():
    req_args = ["key_api", "username", "password", "role"]
    data = json.loads(request.data)
    if (
        helper.args_checker(req_args, data)
        and helper.return_owner_key_data(mongo, data["key_api"])["role"]
        == "admin"
    ):
        register_data = {}
        data["username"] = data["username"].lower().strip()
        if mongo.db.user.find_one(
            {"username": data["username"]}, {}
        ):  # username already exist
            return {"status": "fail", "message": "Username already exist!"}, 409
        register_data["username"] = data["username"]
        register_data["password"] = sha256_crypt.hash(data["password"])
        register_data["role"] = data["role"]
        register_data["my_attendance"] = []

        mongo.db.user.insert_one(register_data)

        return {
            "status": "success",
            "message": "Registered %s as %s"
            % (register_data["username"], register_data["role"]),
        }
    else:
        return {"status": "fail", "message": "Unauthorized Access"}, 400


@app.route("/get_users", methods=["GET"])
def get_users():
    key_api = request.args.get("key_api", "")
    if key_api and helper.return_owner_key_data(mongo, key_api):
        users = list(mongo.db.user.find({}, {"password": 0, "my_attendance": 0}))  # lmao
        return dumps({"status": "success", "users": users}), 200  # this is expansive my dude, maybe you want to not show all at once?
    else:
        return {"status": "fail", "message": "Unauthorized Access"}, 400


@app.route("/manage_user", methods=["GET", "POST"])
def manage_user():
    if request.method == "GET":
        key_api = request.args.get("key_api", "")
        user_id = request.args.get("user_id", "")
        if key_api and helper.return_owner_key_data(mongo, key_api)["role"] == "admin":
            target_user = mongo.db.user.find_one({"_id": ObjectId(user_id)})
            if target_user:
                return dumps({"status": "success", "target_user": target_user}, json_options=RELAXED_JSON_OPTIONS)
            else:
                return {"status": "fail", "message": "Target user does not exist."}, 404
        else:
            return {"status": "fail", "message": "Unauthorized Access"}, 400
    elif request.method == "POST":
        req_args = ["key_api", "new_userdata"]
        data = loads(request.data)
        data["new_userdata"] = loads(data["new_userdata"])
        if helper.args_checker(req_args, data) and helper.return_owner_key_data(mongo, data["key_api"])["role"] == "admin":
            result = mongo.db.user.update_one({"_id": data["_id"]}, {"$set": data["new_userdata"]})
            if result.modified_count != 0:
                return {"status": "success", "message": "User data was updated!"}
            else:
                return {"status": "fail", "message": "You are updating a user that does not exist or you are not updating anything"}, 404
        else:
            return {"status": "fail", "message": "Unauthorized access!"}, 400


@app.route("/reset_password_user", methods=["GET"])
def reset_password():
    # req_args = ["api_key", "user_id"]
    key_api = request.args.get("key_api", "")
    user_id = request.args.get("user_id", "")
    if key_api and user_id and helper.return_owner_key_data(mongo, key_api)["role"] == 'admin':
        new_password = "".join(crypto.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))
        userdata = mongo.db.user.find_one_and_update({"_id": ObjectId(user_id)}, {"$set": {"password": sha256_crypt.hash(new_password)}})
        if userdata:
            mongo.db.key_api.delete_many({"username": userdata["username"]})
            return {"status": "success", "message": "Resetted password for " + userdata["username"], "password": new_password}, 200
        else: 
            return {"status": "fail", "message": "Target user not found"}, 404
    return {"status": "fail", "message": "Unauthorized Access"}, 400


############################################ AUTHENTICATION ##############################
@app.route("/login", methods=["POST"])
def login():
    # my_printer.pprint(request.get_json())
    # print(request.get_json())
    # print(request.data)
    # print(request.form)
    data = json.loads(request.data)
    if not helper.args_checker(["username", "password"], data):
        return {"status": "critical failure", "message": "missing required args"}
    username = data["username"].lower()
    password = data["password"]
    data = mongo.db.user.find_one({"username": username})
    if data and sha256_crypt.verify(password, data["password"]):
        status = True
        key = "".join(
            crypto.choices(
                "abcdefghijklmnpqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", k=42
            )
        )
        mongo.db.key_api.insert_one({"username": username, "key": key})
    else:
        status = False
        key = ""
    return {
        "status": "success" if status else "fail",
        "key": key,
    }, 401 if not status else 200


@app.route("/login_admin", methods=["POST"])
def login_admin():
    data = json.loads(request.data)
    if helper.args_checker(["username", "password"], data):
        user_data = mongo.db.user.find_one({"username": data["username"]})
        if user_data and user_data["role"] == "admin":  # if user exist and is admin
            if sha256_crypt.verify(data["password"], user_data["password"]):
                key = "".join(
                    crypto.choices(
                        "abcdefghijklmnpqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
                        k=42,
                    )
                )
                mongo.db.key_api.insert_one(
                    {"username": user_data["username"], "key": key}
                )

                return {"status": "success", "key": key}
        return {"status": "fail", "message": "Wrong password or username"}, 401
    else:
        return {"status": "fail", "message": "args not enough"}, 400


@app.route("/logout", methods=["DELETE"])  # tengok args lul
def logout():
    key_api = request.args.get("key_api", "")
    if key_api:
        mongo.db.key_api.delete_one({"key": key_api})
        return {"status": "success"}
    else:
        return {"status": "fail", "message": "missing required args"}


################################## EVENT ####################################################
@app.route("/create_event", methods=["PUT"])
def create_event():
    req_args = ["key_api", "event_title", "venue", "datetime", "imageURL", "description"]
    data = json.loads(request.data)
    if helper.args_checker(req_args, data): 
        caller_data = helper.return_owner_key_data(mongo, data["key_api"], verbose=True)
        if caller_data and  caller_data["role"] == "admin":
            event = mongo.db.events.insert_one(
                {
                    "owner": caller_data["username"],
                    "title": data["event_title"],
                    "description": data["description"],
                    "venue": data["venue"],
                    "imageURL": data["imageURL"],
                    "datetime": pytz.timezone("Asia/Kuala_Lumpur").localize(
                        parser.parse(data["datetime"])
                    ),
                    "attendees": [],
                }
            )
            return {"status": "success", "id": str(event.inserted_id)}
        else:
            return {"status": "fail", "message": "unauthorized"}, 401
    else:
        return {"status": "fail", "message": "args not enough"}, 400


@app.route("/attend_event", methods=["POST"])
def attend_event():
    req_args = ["key_api", "event_id"]
    data = json.loads(request.data)
    caller_data = helper.return_owner_key_data(mongo, data["key_api"], verbose=True)
    if helper.args_checker(req_args, data) and caller_data:
        # if 'feedback' not in data:
        #     data['feedback'] = ''
        the_event = mongo.db.events.find_one_or_404(
            {"_id": ObjectId(data["event_id"])}, {"owner": 0, "venue": 0, "datetime": 0}
        )
        for attendee in the_event["attendees"]:
            if attendee["username"] == caller_data["username"]:
                return {"status": "fail", "message": "Already attended."}, 409
        now = datetime.now(pytz.utc)
        if mongo.db.events.find_one_and_update(
            {"_id": ObjectId(data["event_id"])},
            {
                "$push": {
                    "attendees": {
                        "username": caller_data["username"],
                        "datetime": now
                        # "feedback": data['feedback']
                    }
                }
            },
        ):
            mongo.db.user.update_one(
                {"_id": caller_data["_id"]},
                {
                    "$push": {
                        "my_attendance": {
                            "event_id": the_event["_id"],
                            "event_title": the_event["title"],
                            "attendance_time": now,
                        }
                    }
                },
            )
            return {
                "status": success,
                "datetime": now.astimezone(pytz.timezone("Asia/Kuala_Lumpur")).strftime(
                    "%I:%M %p %b %d, %Y"
                ),
            }
        else:
            return {"status": "fail", "message": "event not found"}, 404
    else:
        return {"status": "fail", "message": "args not enough"}, 400


@app.route("/get_events")
def get_events():
    # req_args = ['key_api']
    key_api = request.args.get("key_api", "")
    if key_api and helper.return_owner_key_data(mongo, key_api):
        the_cursor = mongo.db.events.find(
            {}, {"attendees": 0}
        ).sort('datetime', pymongo.DESCENDING)
        the_events = list(the_cursor)
        for event in the_events:
            event["datetime"] = [
                pytz.utc.localize(event["datetime"])
                .astimezone(pytz.timezone("Asia/Kuala_Lumpur"))
                .strftime("%I:%M %p"),
                pytz.utc.localize(event["datetime"])
                .astimezone(pytz.timezone("Asia/Kuala_Lumpur"))
                .strftime("%b %d, %Y"),
            ]
        return_data =  dumps(
            {"status": "success", "results": the_events},
            json_options=RELAXED_JSON_OPTIONS
        )  # event mesti tak banyak hehe
        return return_data
    else:
        return {"status": "fail"}, 401


@app.route("/edit_event", methods=["PATCH"])
def edit_event():
    req_args = ["key_api", "id", "title", "venue", "datetime", "imageURL", "description"]
    data = json.loads(request.data)
    caller_data = helper.return_owner_key_data(mongo, data["key_api"])
    if helper.args_checker(req_args, data) and caller_data["role"] == "admin":
        mongo.db.events.update_one(
            {"_id": ObjectId(data["id"])},
            {
                "$set": {
                    "title": data["title"],
                    "description": data["description"],
                    "venue": data["venue"],
                    "imageURL": data["imageURL"],
                    "datetime": pytz.timezone("Asia_Kuala_Lumpur").localize(
                        parser.parse(data["datetime"])
                    ),
                }
            },
        )
        return {"status": "success", "message": "Successfully edited the event!"}
    return {"status": "fail", "message": "Not enough args or not an admin."}, 400


@app.route("/remove_event", methods=["DELETE"])
def remove_event():
    req_args = ["key_api", "event_id"]
    data = request.args.to_dict()
    caller_data = helper.return_owner_key_data(mongo, data["key_api"])
    if  helper.args_checker(req_args, data) and caller_data["role"] == "admin":
        result = mongo.db.events.remove_one({"_id": ObjectId(data["event_id"])})
        if result.raw_data['n'] == 0:
            return {"status": "fail", "message": "Event was not found."}, 404
        return {"status": "success", "message": "Event deleted."}
    else:
        return {"status": "fail", "message": "Missing required arguements."}, 400


################################# Miscellaneous ####################################
@app.route("/init_db")
def init_db():
    if not mongo.db.user.estimated_document_count():
        mongo.db.user.insert_one(
            {
                "username": "admin",
                "password": sha256_crypt.hash("admin"),
                "role": "admin",
                "my_attendance": []
            }
        )
        return "created the user admin"
    return "admin already existed!", 400


@app.route("/who_am_i", methods=["GET"])
def who_am_i():
    key_api = request.args.get("key_api", "")
    caller_data = helper.return_owner_key_data(mongo, key_api, extra_verbose=True)
    for the_datetime in caller_data["my_attendance"]:
        the_datetime["attendance_time"] = (
            pytz.utc.localize(the_datetime["attendance_time"])
            .astimezone(pytz.timezone("Asia/Kuala_Lumpur"))
            .strftime("%I:%M %p %b %d, %Y")
        )
    return dumps(caller_data, json_options=RELAXED_JSON_OPTIONS)


@app.route("/test_api", methods=["GET", "POST"])
def test_api():
    if request.method == "POST":
        print(request.data)
    return {"message": "thank you"}, 313


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=6969)
