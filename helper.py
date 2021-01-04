def args_checker(args, datajson):
    for arg in args:
        if arg in datajson and datajson[arg]:
            continue
        else:
            return False
    else:
        return True

def return_owner_key_data(mongo, key_api, verbose=False, extra_verbose=False):
    if extra_verbose:
        caller_data = mongo.db.key_api.find_one({'key': key_api})
    elif verbose:
        caller_data = mongo.db.key_api.find_one({'key': key_api}, {'username': 1, 'password': 1, 'role': 1})
    else:
        caller_data = mongo.db.key_api.find_one({'key': key_api}, {"_id": 1})
    
    if caller_data:
        return caller_data
    else:
        return None
    
