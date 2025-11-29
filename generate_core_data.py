"""
Generate sample data for the new core CSV structure
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
CORE_DATA_DIR = Path(__file__).parent / "data" / "core"
NUM_USERS = 25
NUM_TUTORS = 20
NUM_COURSES = 15
NUM_SHIFTS = 30
NUM_APPOINTMENTS = 50

# Sample data pools
FIRST_NAMES = ["Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason", "Isabella", "James",
               "Mia", "Lucas", "Charlotte", "Oliver", "Amelia", "Elijah", "Harper", "Logan", "Evelyn", "Aiden",
               "Abigail", "Jackson", "Emily", "Carter", "Elizabeth", "Jayden", "Sofia", "Sebastian", "Avery", "Michael"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
              "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]

DEPARTMENTS = ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", "Engineering"]

COURSE_SUBJECTS = {
    "Computer Science": ["Python Programming", "Data Structures", "Algorithms", "Web Development", "Database Systems"],
    "Mathematics": ["Calculus I", "Calculus II", "Linear Algebra", "Statistics", "Discrete Math"],
    "Physics": ["Physics I", "Physics II", "Quantum Mechanics", "Thermodynamics"],
    "Chemistry": ["General Chemistry", "Organic Chemistry", "Physical Chemistry"],
    "Biology": ["Cell Biology", "Genetics", "Microbiology", "Biochemistry"],
    "Engineering": ["Engineering Mechanics", "Circuit Analysis", "Thermodynamics", "Fluid Mechanics"]
}

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def generate_id(prefix="", length=6):
    """Generate a random ID"""
    return f"{prefix}{random.randint(10**(length-1), 10**length-1)}"

def generate_email(first_name, last_name):
    """Generate email address"""
    return f"{first_name.lower()}.{last_name.lower()}@university.edu"

def generate_password_hash():
    """Generate a dummy password hash"""
    return "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # SHA256 of 'password'

def generate_time(start_hour=8, end_hour=20):
    """Generate a random time"""
    hour = random.randint(start_hour, end_hour)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}:00"

def generate_users():
    """Generate users.csv"""
    print("Generating users.csv...")
    users = []
    
    # Admin user
    users.append({
        'user_id': 'ADMIN001',
        'email': 'admin@university.edu',
        'password_hash': generate_password_hash(),
        'full_name': 'System Administrator',
        'role': 'admin',
        'is_active': 'True',
        'created_at': datetime.now().isoformat(),
        'last_login': datetime.now().isoformat()
    })
    
    # Generate regular users
    for i in range(NUM_USERS):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        role = 'tutor' if i < NUM_TUTORS else 'staff'
        
        users.append({
            'user_id': f"USER{i+1:04d}",
            'email': generate_email(first_name, last_name),
            'password_hash': generate_password_hash(),
            'full_name': f"{first_name} {last_name}",
            'role': role,
            'is_active': 'True',
            'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
            'last_login': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        })
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'users.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=users[0].keys())
        writer.writeheader()
        writer.writerows(users)
    
    return users

def generate_tutors(users):
    """Generate tutors.csv"""
    print("Generating tutors.csv...")
    tutors = []
    
    tutor_users = [u for u in users if u['role'] == 'tutor']
    
    for idx, user in enumerate(tutor_users[:NUM_TUTORS]):
        tutors.append({
            'tutor_id': generate_id("T", 7),
            'user_id': user['user_id'],
            'bio': f"Experienced tutor specializing in {random.choice(list(COURSE_SUBJECTS.keys()))}",
            'specializations': ','.join(random.sample(list(COURSE_SUBJECTS.keys()), k=random.randint(1, 3))),
            'max_appointments_per_day': random.choice([3, 4, 5, 6]),
            'is_available': 'True',
            'joined_date': (datetime.now() - timedelta(days=random.randint(30, 730))).isoformat()
        })
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'tutors.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tutor_id', 'user_id', 'bio', 'specializations', 
                                                'max_appointments_per_day', 'is_available', 'joined_date'])
        writer.writeheader()
        writer.writerows(tutors)
    
    return tutors

def generate_courses():
    """Generate courses.csv"""
    print("Generating courses.csv...")
    courses = []
    course_id = 1
    
    for dept, subjects in COURSE_SUBJECTS.items():
        for subject in subjects:
            courses.append({
                'course_id': f"CRS{course_id:04d}",
                'course_code': f"{dept[:3].upper()}{random.randint(100, 499)}",
                'course_name': subject,
                'department': dept,
                'description': f"Introduction to {subject}",
                'is_active': 'True',
                'created_at': (datetime.now() - timedelta(days=random.randint(365, 1095))).isoformat()
            })
            course_id += 1
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'courses.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['course_id', 'course_code', 'course_name', 
                                                'department', 'description', 'is_active', 'created_at'])
        writer.writeheader()
        writer.writerows(courses)
    
    return courses

def generate_tutor_courses(tutors, courses):
    """Generate tutor_courses.csv"""
    print("Generating tutor_courses.csv...")
    tutor_courses = []
    tc_id = 1
    
    for tutor in tutors:
        # Assign 2-5 courses per tutor
        assigned_courses = random.sample(courses, k=random.randint(2, 5))
        for course in assigned_courses:
            tutor_courses.append({
                'tutor_course_id': f"TC{tc_id:05d}",
                'tutor_id': tutor['tutor_id'],
                'course_id': course['course_id'],
                'assigned_date': (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat()
            })
            tc_id += 1
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'tutor_courses.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tutor_course_id', 'tutor_id', 'course_id', 'assigned_date'])
        writer.writeheader()
        writer.writerows(tutor_courses)
    
    return tutor_courses

def generate_shifts():
    """Generate shifts.csv"""
    print("Generating shifts.csv...")
    shifts = []
    
    # Generate various shift times
    shift_times = [
        ("Morning Shift", "08:00:00", "12:00:00"),
        ("Afternoon Shift", "12:00:00", "16:00:00"),
        ("Evening Shift", "16:00:00", "20:00:00"),
        ("Extended Morning", "08:00:00", "14:00:00"),
        ("Extended Evening", "14:00:00", "20:00:00"),
        ("Short Morning", "09:00:00", "11:00:00"),
        ("Short Afternoon", "13:00:00", "15:00:00"),
        ("Short Evening", "17:00:00", "19:00:00")
    ]
    
    shift_id = 1
    for name, start, end in shift_times:
        for day_combo in [
            "Monday,Wednesday,Friday",
            "Tuesday,Thursday",
            "Monday,Tuesday,Wednesday,Thursday,Friday",
            "Saturday,Sunday",
            "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday"
        ]:
            shifts.append({
                'shift_id': f"SH{shift_id:04d}",
                'shift_name': f"{name} - {day_combo.split(',')[0]}",
                'start_time': start,
                'end_time': end,
                'days_of_week': day_combo,
                'created_by': 'ADMIN001',
                'created_at': (datetime.now() - timedelta(days=random.randint(30, 180))).isoformat(),
                'active': 'True'
            })
            shift_id += 1
            if shift_id > NUM_SHIFTS:
                break
        if shift_id > NUM_SHIFTS:
            break
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'shifts.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['shift_id', 'shift_name', 'start_time', 'end_time', 
                                                'days_of_week', 'created_by', 'created_at', 'active'])
        writer.writeheader()
        writer.writerows(shifts)
    
    return shifts

def generate_shift_assignments(shifts, tutors, users):
    """Generate shift_assignments.csv"""
    print("Generating shift_assignments.csv...")
    assignments = []
    assignment_id = 1
    
    for tutor in tutors:
        # Get tutor's full name from users
        user = next((u for u in users if u['user_id'] == tutor['user_id']), None)
        tutor_name = user['full_name'] if user else "Unknown"
        
        # Assign 1-3 shifts per tutor
        assigned_shifts = random.sample(shifts, k=random.randint(1, 3))
        for shift in assigned_shifts:
            start_date = datetime.now() - timedelta(days=random.randint(0, 30))
            end_date = start_date + timedelta(days=random.randint(30, 90))
            
            assignments.append({
                'assignment_id': f"SA{assignment_id:05d}",
                'shift_id': shift['shift_id'],
                'tutor_id': tutor['tutor_id'],
                'tutor_name': tutor_name,
                'start_date': start_date.date().isoformat(),
                'end_date': end_date.date().isoformat(),
                'assigned_by': 'ADMIN001',
                'assigned_at': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                'active': 'True'
            })
            assignment_id += 1
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'shift_assignments.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['assignment_id', 'shift_id', 'tutor_id', 'tutor_name', 
                                                'start_date', 'end_date', 'assigned_by', 'assigned_at', 'active'])
        writer.writeheader()
        writer.writerows(assignments)
    
    return assignments

def generate_availability(tutors):
    """Generate availability.csv"""
    print("Generating availability.csv...")
    availabilities = []
    avail_id = 1
    
    for tutor in tutors:
        # Generate 2-4 availability windows per tutor
        num_windows = random.randint(2, 4)
        for _ in range(num_windows):
            day = random.choice(DAYS_OF_WEEK)
            start_hour = random.randint(8, 15)
            end_hour = start_hour + random.randint(2, 6)
            
            availabilities.append({
                'availability_id': f"AV{avail_id:05d}",
                'tutor_id': tutor['tutor_id'],
                'day_of_week': day,
                'start_time': f"{start_hour:02d}:00:00",
                'end_time': f"{end_hour:02d}:00:00",
                'is_recurring': 'True',
                'effective_date': (datetime.now() - timedelta(days=random.randint(0, 30))).date().isoformat(),
                'end_date': (datetime.now() + timedelta(days=random.randint(60, 180))).date().isoformat()
            })
            avail_id += 1
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'availability.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['availability_id', 'tutor_id', 'day_of_week', 'start_time', 
                                                'end_time', 'is_recurring', 'effective_date', 'end_date'])
        writer.writeheader()
        writer.writerows(availabilities)
    
    return availabilities

def generate_appointments(tutors, courses):
    """Generate appointments.csv"""
    print("Generating appointments.csv...")
    appointments = []
    
    student_names = [f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}" for _ in range(30)]
    statuses = ['scheduled', 'completed', 'cancelled', 'no-show']
    
    for i in range(NUM_APPOINTMENTS):
        tutor = random.choice(tutors)
        course = random.choice(courses)
        student_name = random.choice(student_names)
        
        appt_date = datetime.now() - timedelta(days=random.randint(-30, 30))
        start_hour = random.randint(8, 18)
        end_hour = start_hour + random.randint(1, 3)
        
        appointments.append({
            'appointment_id': f"APT{i+1:05d}",
            'tutor_id': tutor['tutor_id'],
            'student_name': student_name,
            'student_email': student_name.lower().replace(' ', '.') + '@student.edu',
            'course_id': course['course_id'],
            'appointment_date': appt_date.date().isoformat(),
            'start_time': f"{start_hour:02d}:00:00",
            'end_time': f"{end_hour:02d}:00:00",
            'status': random.choice(statuses),
            'notes': random.choice(['Help with homework', 'Exam preparation', 'Project discussion', 'General questions', '']),
            'created_at': (appt_date - timedelta(days=random.randint(1, 7))).isoformat(),
            'updated_at': appt_date.isoformat()
        })
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'appointments.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['appointment_id', 'tutor_id', 'student_name', 'student_email', 
                                                'course_id', 'appointment_date', 'start_time', 'end_time', 
                                                'status', 'notes', 'created_at', 'updated_at'])
        writer.writeheader()
        writer.writerows(appointments)
    
    return appointments

def generate_audit_log(users):
    """Generate audit_log.csv"""
    print("Generating audit_log.csv...")
    audit_logs = []
    
    actions = ['login', 'logout', 'create', 'update', 'delete', 'view']
    resource_types = ['user', 'tutor', 'course', 'shift', 'appointment', 'assignment']
    
    for i in range(100):
        user = random.choice(users)
        action = random.choice(actions)
        resource_type = random.choice(resource_types)
        
        audit_logs.append({
            'log_id': f"LOG{i+1:06d}",
            'user_id': user['user_id'],
            'action': action,
            'resource_type': resource_type,
            'resource_id': f"{resource_type.upper()}{random.randint(1, 100):04d}",
            'details': f"{action.capitalize()} {resource_type}",
            'ip_address': f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            'timestamp': (datetime.now() - timedelta(days=random.randint(0, 30), 
                                                     hours=random.randint(0, 23), 
                                                     minutes=random.randint(0, 59))).isoformat()
        })
    
    # Sort by timestamp
    audit_logs.sort(key=lambda x: x['timestamp'])
    
    # Write to CSV
    with open(CORE_DATA_DIR / 'audit_log.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['log_id', 'user_id', 'action', 'resource_type', 
                                                'resource_id', 'details', 'ip_address', 'timestamp'])
        writer.writeheader()
        writer.writerows(audit_logs)
    
    return audit_logs

def main():
    """Main function to generate all data"""
    print("=" * 60)
    print("Generating Core Data for New CSV Structure")
    print("=" * 60)
    
    # Ensure core directory exists
    CORE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate data in proper order (respecting foreign key relationships)
    users = generate_users()
    tutors = generate_tutors(users)
    courses = generate_courses()
    tutor_courses = generate_tutor_courses(tutors, courses)
    shifts = generate_shifts()
    shift_assignments = generate_shift_assignments(shifts, tutors, users)
    availabilities = generate_availability(tutors)
    appointments = generate_appointments(tutors, courses)
    audit_logs = generate_audit_log(users)
    
    print("\n" + "=" * 60)
    print("Data Generation Complete!")
    print("=" * 60)
    print(f"Users: {len(users)}")
    print(f"Tutors: {len(tutors)}")
    print(f"Courses: {len(courses)}")
    print(f"Tutor-Course Assignments: {len(tutor_courses)}")
    print(f"Shifts: {len(shifts)}")
    print(f"Shift Assignments: {len(shift_assignments)}")
    print(f"Availability Windows: {len(availabilities)}")
    print(f"Appointments: {len(appointments)}")
    print(f"Audit Log Entries: {len(audit_logs)}")
    print("=" * 60)
    print(f"\nAll data saved to: {CORE_DATA_DIR}")
    print("\nNote: Default password for all users is 'password'")

if __name__ == "__main__":
    main()

