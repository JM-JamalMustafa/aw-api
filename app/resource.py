# app/resource.py

from flask_restx import Resource, fields, Namespace
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token,get_jwt
from peewee import DoesNotExist
import bcrypt
from app.model import User, Activity, Event, db  # Directly import models from `model.py`
from datetime import datetime
from peewee import IntegrityError

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
                timestamp = datetime.fromisoformat(event['timestamp'])  # Assuming ISO8601 format
                duration = event['duration']
                app_name = event['data']['app']
                title = event['data'].get('title', '')  # Optional title field
                
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
                    user=user  # Associate event with the current user instance
                )
                events_to_store.append(new_event)
            except KeyError as e:
                return {'message': f"Missing key in event data: {str(e)}"}, 400
            except ValueError as e:
                return {'message': f"Invalid value in event data: {str(e)}"}, 400

        # Bulk insert events into the database
        try:
            Event.bulk_create(events_to_store)  # Efficient bulk insert
        except Exception as e:
            return {'message': f"Failed to store events: {str(e)}"}, 500

        return {'message': 'Data stored successfully', 'stored_count': len(events_to_store)}, 201

    
# Fetch data from aw-server using this class 
# class FetchAWServerData:
#     """Background thread for fetching data from aw-server periodically."""
#     def __init__(self):
#         self.stop_event = threading.Event()

#     def start(self):
#         threading.Thread(target=self._fetch_data_periodically, daemon=True).start()

#     def stop(self):
#         self.stop_event.set()

#     def _fetch_data_periodically(self):
#         while not self.stop_event.is_set():
#             try:
#                 self.fetch_data_from_aw_server(self)
#             except Exception as e:
#                 print(f"Error fetching data from aw-server: {e}")
#             self.stop_event.wait(FETCH_INTERVAL)

#     def fetch_data_from_aw_server(self, user):
#         """Fetch data from the user's AW server using hostname and save to the centralized database."""
#         try:
            

#             # Step 1: Get the hostname dynamically
#             hostname = socket.gethostname()  # Use socket.gethostname() to retrieve the current machine's hostname

#             # Step 2: Use the hostname to fetch events from the bucket
#             bucket_url = f"{aw_server_url}/api/0/buckets/aw-watcher-window_{hostname}/events?limit=10"
#             response = requests.get(bucket_url)
#             if response.status_code == 200:
#                 data = response.json()
#                 self._process_aw_data(data, user)
#             else:
#                 print(f"Failed to fetch data: {response.status_code}, {response.text}")
#         except requests.exceptions.RequestException as e:
#             print(f"Connection error: {e}")



#     def _process_aw_data(self, events_data, username):
#         """Process and save the fetched event data into the centralized database."""
#         if not events_data or not isinstance(events_data, list):
#             print("Invalid data received from aw-server. Expected a list of events.")
#             return

#         # Process each event
#         for event in events_data:
#             event_data = event.get("data", {})
#             timestamp = event.get("timestamp")
#             duration = event.get("duration")

#             app_name = event_data.get("app", "Unknown app")
#             title = event_data.get("title", "Untitled")

#             try:
                
#                 user = User.get_or_none(User.username == username)
#                 if user:
#                     Activity.create(
#                         user=user,
#                         timestamp=timestamp,
#                         duration=duration,
#                         data={"app": app_name, "title": title}
#                     )
#                     print(f"Successfully processed event: {event}")
#                 else:
#                     print(f"User not found for event: {event}")
#             except Exception as e:
#                 print(f"Error saving event: {str(e)}")

# endpoint to get data and store in database
# class FetchActivityDataEndpoint(Resource):
#     """Endpoint to trigger fetching data from AW-Server."""

#     @jwt_required()  
#     def get(self):
#         """Fetch data from the AW-Server and save it to the centralized database."""
#         try:
#             # Fetch the user identity from JWT
#             username = get_jwt_identity()  
#             fetcher = FetchAWServerData()
#             fetcher.fetch_data_from_aw_server(username)  
#             return {"message": "Data fetched and processed successfully."}, 200
#         except Exception as e:
#             return {"message": f"Error fetching data: {str(e)}"}, 500

        
class Logout(Resource):
    @jwt_required()
    def post(self):
        """Logout Endpoint - Blacklist the token"""
        jti = get_jwt()["jti"]  # Get the unique identifier for the token
        BLACKLIST.add(jti)  # Add the token identifier to the blacklist
        return {'message': 'Successfully logged out'}, 200

