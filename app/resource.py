# app/resource.py

from flask_restx import Resource, fields, Namespace
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token,get_jwt
from peewee import DoesNotExist
import bcrypt
from app.model import User, Activity, Event, db  # Directly import models from `model.py`
from datetime import datetime
from peewee import IntegrityError
from flask import request, jsonify, current_app
from werkzeug.exceptions import BadRequest
import logging
from app.settings import Settings
from app.api import ServerAPI

logger = logging.getLogger(__name__)

# Define your namespace for the API
ns = Namespace('events', description='Event-related operations')

# Store blacklisted tokens (In-memory or better use a database/redis for production)
BLACKLIST = set()

class Register(Resource):
    def post(self):
        data = request.get_json()
        username = data['username']
        password = data['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            User.create(username=username, password=hashed_password)
            return {'message': 'User registered successfully!'}, 201
        except IntegrityError:
            return {'message': 'Username already exists'}, 400

class Login(Resource):
    def post(self):
        """Login Endpoint"""
        data = request.get_json()
        username = data['username']
        password = data['password']

        user = User.get_or_none(User.username == username)
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            access_token = create_access_token(identity=username)
            return {'access_token': access_token}, 200
        return {'message': 'Invalid username or password'}, 401

class ChangePassword(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        new_password = data['password']
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        user_identity = get_jwt_identity()  # Get current user from JWT
        try:
            user = User.get(User.username == user_identity)  # Use username from JWT identity
            user.password = hashed_password
            user.save()
            return {'message': 'Password updated successfully'}, 200
        except DoesNotExist:
            return {'message': 'User not found'}, 404



class SubmitData(Resource):
    @jwt_required()  # Ensure the user is authenticated
    def post(self):
        """
        Submit event data to be stored in the centralized database, associated with the logged-in user.
        """
        # Get the current user from the JWT token
        user_identity = get_jwt_identity()

        # Get the JSON data from the request
        data = request.get_json()

        # If the data is a single event, make it a list
        if isinstance(data, dict):
            data = [data]

        events_to_store = []
        for event in data:
            try:
                # Extract required fields from event data
                timestamp = datetime.fromisoformat(event['timestamp']) 
                duration = event['duration']
                app_name = event['data']['app']
                title = event['data'].get('title', '')  
                client = event.get('client', 'unknown') 
                # Attempt to get the user based on the JWT identity (username)
                try:
                    user = User.get(User.username == user_identity)  # Fetch user by username (from JWT)
                except DoesNotExist:
                    return {'message': f"User with username {user_identity} does not exist."}, 404
                
                # Create a new Event object and associate it with the current user
                new_event = Event(
                    timestamp=timestamp, 
                    duration=duration, 
                    app=app_name, 
                    title=title, 
                    user=user,
                    client = client # Associate event with the current user instance
                )
                events_to_store.append(new_event)
            except KeyError as e:
                return {'message': f"Missing key in event data: {str(e)}"}, 400
            except ValueError as e:
                return {'message': f"Invalid value in event data: {str(e)}"}, 400

        # Bulk insert events into the database
        try:
            Event.bulk_create(events_to_store)  
        except Exception as e:
            return {'message': f"Failed to store events: {str(e)}"}, 500

        return {'message': 'Data stored successfully', 'stored_count': len(events_to_store)}, 201
        
class Logout(Resource):
    @jwt_required()
    def post(self):
        """Logout Endpoint - Blacklist the token"""
        jti = get_jwt()["jti"]  # Get the unique identifier for the token
        BLACKLIST.add(jti)  # Add the token identifier to the blacklist
        return {'message': 'Successfully logged out'}, 200

class AdminFetchEvents(Resource):
    @jwt_required()  
    def get(self):
        """
        Endpoint to fetch events for the authenticated admin user.
        The events will be fetched based on the JWT identity (username).
        """
        # Get the current user's identity (username) from the JWT token
        admin_username = get_jwt_identity()

        # Get query parameters
        limit = request.args.get('limit', None)

        # Validate limit
        try:
            limit = int(limit) if limit else None
        except ValueError:
            return {'message': 'Invalid limit value'}, 400

        # Fetch events for the authenticated admin user
        event_query = (
            Event.select(Event, User)
            .join(User)
            .where(User.username == admin_username)  
            .order_by(Event.timestamp.desc())  
        )

        # Apply limit if specified
        if limit:
            event_query = event_query.limit(limit)

        # Format the events into a response
        events = [
            {
                'id': event.id,
                'timestamp': datetime.fromisoformat(event.timestamp).isoformat(),  
                'duration': event.duration,
                'app': event.app,
                'title': event.title,
                'client': event.client,  
                'user': event.user.username,  
            }
            for event in event_query
        ]

        # Return the list of events along with the total count
        return {'events': events, 'count': len(events)}, 200


class SettingsResource(Resource):
    def get(self, key: str):
        # Ensure current_app.api exists
        if not hasattr(current_app, 'api'):
            return {"message": "API not initialized"}, 500
        
        data = current_app.api.get_setting(key)  # Access the settings
        return jsonify(data)

    def post(self, key: str):
        if not key:
            raise BadRequest("MissingParameter", "Missing required parameter key")
        data = current_app.api.set_setting(key, request.get_json())
        return data