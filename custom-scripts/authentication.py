from flask_restful import Resource

class Authentication(Resource):
    def get(self):
        return {"data": "Hello world!"}
