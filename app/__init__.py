# app/__init__.py

from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager, get_jwt_identity
from flask_restx import Api, fields,Namespace
from app.model import initialize_db,db
from app.resource import Register, Login, ChangePassword,Logout,SubmitData,ns,AdminFetchEvents,SettingsResource
from datetime import timedelta
from cachetools import TTLCache
from app.api import ServerAPI
# Initialize Flask app
app = Flask(__name__)

# Define the route for the base IP ('/')
@app.route('/')
def home():
    return "APIs are working on the central server"

<<<<<<< HEAD


testing = app.config["TESTING"]
app.config["JWT_SECRET_KEY"] = "40e1a1c45a2eac697b9f5fb419adbe4c"
=======
app.config["JWT_SECRET_KEY"] = "your_key"
>>>>>>> be11f6f75d2438e236787ed9af08215c7a4aa58a
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)
jwt = JWTManager(app)
api = Api(app, doc='/docs')  # Swagger UI will be available at /docs instead of the root

# Cache with an 8-hour expiration
jwt_cache = TTLCache(maxsize=100, ttl=28800)

# Initialize JWT
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")
# Initialize the database (connect and create tables)
initialize_db()

# Define the model schemas here
user_model = api.model('User', {
    'username': fields.String(required=True, description="The user's username"),
    'password': fields.String(required=True, description="The user's password")
})


# Define the Event model schema for request validation (this should match your Event model)
event_model = ns.model('Event', {
    'timestamp': fields.String(required=True, description='Timestamp of the event (ISO 8601 format)'),
    'duration': fields.Integer(required=True, description='Duration of the event in seconds'),
    'data': fields.Nested(
        ns.model('EventData', {
            'app': fields.String(required=True, description='Application name'),
            'title': fields.String(description='Window title or metadata', default=''),
        })
    ),
})


# Register routes here
api.add_resource(Register, '/api/register')
api.add_resource(Login, '/api/login')
api.add_resource(ChangePassword, '/api/change-password')
api.add_resource(Logout, '/api/logout')
api.add_resource(SubmitData,'/api/submit')
<<<<<<< HEAD
api.add_resource(AdminFetchEvents, '/api/fetch')
api.add_resource(SettingsResource, '/api/settings', defaults={"key": ""})
api.add_resource(SettingsResource, '/api/settings/<string:key>')


app.api = ServerAPI(db, testing)
=======
>>>>>>> be11f6f75d2438e236787ed9af08215c7a4aa58a
