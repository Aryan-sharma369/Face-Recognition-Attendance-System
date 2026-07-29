import os, io, csv
from flask import Flask, render_template, Response, jsonify, make_response, request, redirect, url_for
from models import db, Student, Attendance
from face_module.face_engine import FaceRecognitionSystemWeb
from sqlalchemy import func
from datetime import datetime

app = Flask(__name__)


base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'attendance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'known_faces')


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)

with app.app_context():
    db.create_all()


frs = None
try:
    print("--- Starting AI Face Recognition Engine... ---")
    frs = FaceRecognitionSystemWeb(app)
except Exception as e:
    print(f"--- Camera Error: {e} ---")



@app.route('/')
def index():
    students = Student.query.all()

    TARGET_GOAL = 10 
    
    report = {}
    total_perc = 0
    for s in students:
        p_count = len(s.attendances) 
      
        perc = round((p_count / TARGET_GOAL) * 100, 1)
        if perc > 100: perc = 100 
        
        total_perc += perc
        report[s.name] = {
            "present": p_count, 
            "perc": perc, 
            "status": "Regular" if perc >= 75 else "Shortage"
        }
    
    avg = round(total_perc / len(students), 1) if students else 0
    return render_template('index.html', report=report, avg=avg)

@app.route('/api/refresh_data')
def refresh_data():
    try:
        students = Student.query.all()
        TARGET_GOAL = 10 
        
        report_data = {}
        total_perc = 0
        for s in students:
            p_count = len(s.attendances)
            perc = round((p_count / TARGET_GOAL) * 100, 1)
            if perc > 100: perc = 100
            
            total_perc += perc
            report_data[s.name] = {
                "percentage": perc,
                "count": p_count,
                "status": "Regular" if perc >= 75 else "Shortage"
            }
            
        avg_attendance = round(total_perc / len(students), 1) if students else 0
        return jsonify({"students": report_data, "avg": avg_attendance})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/video_feed')
def video_feed():
    """Streams the AI Camera to the UI."""
    if not frs: 
        return "Camera Hardware Offline", 500
    return Response(frs.generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles adding new students and uploading their photo."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip().title()
        roll = request.form.get('roll_number', '').strip() # Added Roll Number support
        file = request.files.get('image')
        
        if name and file:
            # 1. Save Image
            filename = f"{name}.jpg"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # 2. Update Database
            existing = Student.query.filter_by(name=name).first()
            if not existing:
                new_student = Student(name=name, roll_number=roll)
                db.session.add(new_student)
            else:
                existing.roll_number = roll # Update roll if name exists
                
            db.session.commit()
            
           
            if frs: 
                frs.load_known_faces()
                
            return render_template('register.html', success=True)
            
    return render_template('register.html')

@app.route('/export_csv')
def export_csv():
    """Generates a downloadable CSV of all attendance logs."""
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Student Name', 'Date', 'Time'])
    
    records = db.session.query(Student.name, Attendance.date, Attendance.timestamp).join(Attendance).all()
    for r in records:
        cw.writerow([r.name, r.date, r.timestamp.strftime('%H:%M:%S')])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=attendance_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/students')
def students_list():
    """Shows a table of all registered students."""
    return render_template('students.html', students=Student.query.all())

if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)