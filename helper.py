def args_checker(args, datajson):
    for arg in args:
        if arg in datajson and datajson[arg]:
            continue
        else:
            return False
    else:
        return True

def return_owner_key_data(mongo, key_api, verbose=False, extra_verbose=False):
    key_document = mongo.db.key_api.find_one({'key': key_api})
    if key_document["username"]:
        if extra_verbose:
            caller_data = mongo.db.user.find_one({"username": key_document["username"]})
        elif verbose:
            caller_data = mongo.db.user.find_one({"username": key_document["username"]}, {'username': 1, 'password': 1, 'role': 1})
        else:
            caller_data = mongo.db.user.find_one({"username": key_document["username"]}, {"_id": 1, "role": 1})
        return caller_data
    else:
        return None
    
