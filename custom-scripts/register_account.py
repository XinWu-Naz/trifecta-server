from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.tritek
from passlib.hash import sha256_crypt

username = input("Username: ")
password = input("Password: ")

role = input("Role(admin or member): ")

data = {'username': username, 'password': sha256_crypt.hash(password), 'role': role, 'my_attendance': []}

db.user.insert_one(data)