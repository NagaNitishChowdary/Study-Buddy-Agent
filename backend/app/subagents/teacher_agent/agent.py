from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
import os
from dotenv import load_dotenv
from ...db_utils import TeacherDatabase, StudentDatabase

load_dotenv()

# --- Teacher Tools ---

def check_teacher(staff_id: int) -> dict:
    """Check whether a teacher exists in the database.

    Args:
        staff_id: Numeric staff ID.

    Returns:
        A dict with keys:
        - "exists": bool indicating presence of the teacher.
        - "message": human-readable message.
    """
    db = TeacherDatabase()

    if db.teacher_exists(staff_id):
        return {
            "exists": True,
            "message": f"Welcome back! Staff ID {staff_id} found. Would you like to:\\n1. View Profile\\n2. View Student Profile\\n3. Get Class Average"
        }
    else:
        return {
            "exists": False,
            "message": "New Teacher Detected. Please provide your Name, Grades you teach (e.g., [5, 6, 7]), and Subject."
        }

def save_teacher_profile(staff_id: int, name: str, grades: list, subject: str) -> dict:
    """Save a new teacher profile.

    Args:
        staff_id: Teacher's staff ID.
        name: Teacher's name.
        grades: List of grades taught (e.g., [5, 6, 7]).
        subject: Subject taught.

    Returns:
        A dict signalling success or error.
    """
    db = TeacherDatabase()
    result = db.save_teacher(staff_id, name, grades, subject)
    return result

def view_teacher_profile(staff_id: int) -> dict:
    """Retrieve teacher profile data.

    Args:
        staff_id: Teacher's staff ID.

    Returns:
        A dict with teacher profile data.
    """
    db = TeacherDatabase()
    teacher = db.get_teacher(staff_id)
    
    if not teacher:
        return {"status": "error", "message": f"Staff ID {staff_id} not found."}
        
    return {"status": "success", "message": teacher}

def update_teacher_profile(staff_id: int, name: str = None, grades: list = None, subject: str = None) -> dict:
    """Update teacher profile.

    Args:
        staff_id: Teacher's staff ID.
        name: Updated name (optional).
        grades: Updated grades list (optional).
        subject: Updated subject (optional).

    Returns:
        A dict signalling success or error.
    """
    db = TeacherDatabase()
    result = db.update_teacher(staff_id, name, grades, subject)
    return result

def view_student_profile_for_teacher(rollno: int) -> dict:
    """Retrieve student profile data for a teacher.

    Args:
        rollno: Student's roll number.

    Returns:
        A dict with student profile data.
    """
    db = StudentDatabase()
    current_data = db.get_student(rollno)

    if not current_data:
        return {"status": "error", "message": f"Roll No {rollno} not found."}

    current_student = {
        "RollNo": rollno,
        "Name": current_data['Name'],
        "Grade": current_data["Grade"],
        "Language": current_data["Language"],
        "Language1": current_data.get("Language1", 0),
        "Language2": current_data.get("Language2", 0),
        "Language3": current_data.get("Language3", 0),
        "Maths": current_data.get("Maths", 0),
        "Science": current_data.get("Science", 0),
        "Social": current_data.get("Social", 0),
        "TimeStamp": current_data.get("TimeStamp")
    }

    return {"status": "success", "message": current_student}

def get_class_average(grade: int, subject: str) -> dict:
    """Get class average for a subject.

    Args:
        grade: Grade level.
        subject: Subject name.

    Returns:
        A dict with class average statistics.
    """
    db = TeacherDatabase()
    result = db.get_class_average(grade, subject)
    return result

# --- Teacher Agent Definition ---

teacher_agent = LlmAgent(
    name="teacher_agent",
    model=os.getenv("MODEL", "gemini-2.0-flash-exp"),
    description="Agent for Teachers to manage profiles, view student data, and analyze class performance.",
    instruction="""
    You are the Teacher Assistant Agent.
    You help teachers manage their profiles, track student performance, and analyze class results.

    ================================================================================
    GOALS
    ================================================================================
    - Manage teacher profiles (create/update/view)
    - Allow teachers to view specific student profiles
    - Provide class analytics (average scores)
    - Be professional, helpful, and data-driven

    ================================================================================
    INTERACTION FLOW
    ================================================================================

    -----------------------------------
    1) Teacher Identification
    -----------------------------------
    - If the user provides a Staff ID (e.g., "501", "ID 102"):
      - Call `check_teacher(staff_id=<INT>)` IMMEDIATELY.
      - Return the result from `check_teacher` to the user.
      - DO NOT ask for the ID again.
    
    - If the user says "Teacher" but NO ID:
      - Ask: "Please provide your Staff ID."

    -----------------------------------
    2) New Teacher Registration
    -----------------------------------
    - If `check_teacher` returns exists=False:
      - Collect: Name, Grades (list of integers), Subject (one string).
      - Call `save_teacher_profile(staff_id, name, grades, subject)`.
      - Confirm registration.

    -----------------------------------
    3) Existing Teacher Actions
    -----------------------------------
    - If `check_teacher` returns exists=True, offer options:
      a) View My Profile
      b) Update My Profile
      c) View Student Profile
      d) Get Class Average

    ~~~~
    3.a) View My Profile
    ~~~~
    - Call `view_teacher_profile(staff_id)`.
    - Display Name, Grades, Subject.

    ~~~~
    3.b) Update My Profile
    ~~~~
    - Ask what to update (Name, Grades, Subject).
    - Call `update_teacher_profile(...)`.

    ~~~~
    3.c) View Student Profile
    ~~~~
    - Ask for Student Roll Number.
    - Call `view_student_profile_for_teacher(rollno)`.
    - Display student details and scores.

    ~~~~
    3.d) Get Class Average
    ~~~~
    - Ask for Grade and Subject.
    - Call `get_class_average(grade, subject)`.
    - Display average score, student count, min/max scores.

    ================================================================================
    DISPLAY FORMATS
    ================================================================================

    **Teacher Profile:**
    ```
    👨‍🏫 Teacher Profile:
    Name: [Name]
    Staff ID: [ID]
    Subject: [Subject]
    Grades Taught: [Grade1, Grade2, ...]
    ```

    **Class Analytics:**
    ```
    📊 Class Performance Report:
    Grade: [Grade]
    Subject: [Subject]
    
    Average Score: [Score]/100
    Highest Score: [Max]
    Lowest Score: [Min]
    Total Students: [Count]
    ```
    """,
    tools=[
        check_teacher,
        save_teacher_profile,
        view_teacher_profile,
        update_teacher_profile,
        view_student_profile_for_teacher,
        get_class_average
    ]
)
