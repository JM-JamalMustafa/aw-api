from peewee import (
    Model,
    SqliteDatabase,
    CharField,
    TextField,
    DateTimeField,
    IntegerField,
    ForeignKeyField  
)
from datetime import datetime

# Database initialization
db = SqliteDatabase('activity.db')

# Define the User model
class User(Model):
    username = CharField(unique=True)
    password = CharField()

    class Meta:
        database = db

# Define the Activity model
class Activity(Model):
    user = ForeignKeyField(User, backref='activities')  
    data = TextField()  # JSON-encoded data as text
    timestamp = DateTimeField(default=datetime.utcnow)
    duration = IntegerField(null=True) 

    class Meta:
        database = db

# Define the Event model
class Event(Model):
    user = ForeignKeyField(User, backref='events')
    timestamp = DateTimeField()
    duration = IntegerField()  # Duration in seconds (can also be a FloatField if fractional durations)
    app = CharField()
    title = CharField(null=True)
    client = CharField(null=True)  # Foreign key reference to bucket (assuming bucket_id 
     # Back reference to 'events'

    class Meta:
        database = db

# Connect and create tables
def initialize_db():
    db.connect()
    db.create_tables([User, Activity, Event], safe=True)
