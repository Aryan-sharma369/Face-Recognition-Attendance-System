import os
import smtplib
from dotenv import load_dotenv # Run: pip install python-dotenv
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from threading import Thread
from models import db, Student, Attendance

# Load secrets from the .env file
load_dotenv()

# --- 1. SECURE CONFIGURATION ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SMTP_EMAIL")
SENDER_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_async_email(receiver_email, student_name, percentage):
    try:
        body = f"""
        Dear Parent/Guardian,
        
        Attendance alert for {student_name}.
        Current Attendance: {percentage}%
        Status: ATTENDANCE SHORTAGE (Below 75% Threshold)
        
        FaceID Pro Attendance System.
        """
        
        msg = MIMEText(body)
        msg['Subject'] = f"URGENT: Attendance Alert - {student_name}"
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            
        print(f"AUTOMATION: Email alert successfully sent to {receiver_email}")
        
    except Exception as e:
        print(f"MAIL ERROR: {e}")

def mark_attendance(app, name):
    with app.app_context():
        try:
            student = Student.query.filter_by(name=name).first()
            if not student: return False

            new_entry = Attendance(student_id=student.id)
            db.session.add(new_entry)
            db.session.commit()

            # Automation Logic
            TARGET_GOAL = 10 
            present_count = len(student.attendances)
            percentage = round((present_count / TARGET_GOAL) * 100, 1)

            if percentage < 75:
                cooldown_limit = datetime.now() - timedelta(hours=24)
                
                if student.last_notified is None or student.last_notified < cooldown_limit:
                    # FIX: Use the actual email from the database
                    # Fallback to your email if student doesn't have one set
                    receiver = student.parent_email if student.parent_email else SENDER_EMAIL
                    
                    Thread(target=send_async_email, args=(receiver, student.name, percentage)).start()
                    
                    student.last_notified = datetime.now()
                    db.session.commit()

            return True
        except Exception as e:
            print(f"DATABASE ERROR: {e}")
            db.session.rollback()
            return False