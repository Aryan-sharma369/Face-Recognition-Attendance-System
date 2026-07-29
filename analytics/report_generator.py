
import csv
from collections import defaultdict

def calculate_attendance():
    attendance_data = defaultdict(set)
    try:
        with open("attendance.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                attendance_data[row["Name"]].add(row["Date"])
    except FileNotFoundError:
        return {}

    all_dates = set()
    for dates in attendance_data.values():
        all_dates.update(dates)
    total_days = len(all_dates)

    report = {}
    for name, dates in attendance_data.items():
        present_days = len(dates)
        percentage = (present_days / total_days) * 100 if total_days > 0 else 0

        status = "Regular" if percentage >= 75 else "Shortage"

        report[name] = {
            "present_days": present_days,
            "total_days": total_days,
            "percentage": round(percentage, 2),
            "status": status
        }
    return report
