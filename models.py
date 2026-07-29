from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    roll_number = db.Column(db.String(20), unique=True)
    
    # NEW: Store parent's email for alerts
    parent_email = db.Column(db.String(120), nullable=True)
    
    last_notified = db.Column(db.DateTime, nullable=True) 
    attendances = db.relationship('Attendance', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    # FIX: Pass the function name (datetime.now) without () 
    # so it calculates the time WHEN the record is created, not when the server starts.
    timestamp = db.Column(db.DateTime, default=datetime.now)
    date = db.Column(db.Date, default=lambda: datetime.now().date())