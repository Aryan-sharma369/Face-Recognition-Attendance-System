from main import app, db
from models import Student

with app.app_context():
    # List the names exactly as they appear in your 'known_faces' filenames
    students_to_add = ["Virat Kohli", "Cristiano", "Elon Musk"]
    
    for name in students_to_add:
        existing = Student.query.filter_by(name=name).first()
        if not existing:
            new_student = Student(name=name) # type: ignore
            db.session.add(new_student)
            print(f"Added {name} to database.")
    
    db.session.commit()
    print("Database Initialized!")