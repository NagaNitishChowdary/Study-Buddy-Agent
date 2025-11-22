from google.adk.agents import Agent
import os 

from dotenv import load_dotenv
load_dotenv()
from ...db_utils import StudentCourseRecommendationDatabase

def display_student_tutorials(rollno: int) -> str:
    """Return a human-readable list of recommended YouTube tutorials for a student.

    Args:
        rollno: Numeric identifier for a student (roll number).

    Returns:
        A string listing recommended YouTube tutorials grouped by subject,
        or a message stating no recommendations were found for the given student.
    """
    cdb = StudentCourseRecommendationDatabase()
    courses = cdb.get_courses_for_student(rollno)

    if not courses:
        return f"No recommended YouTube tutorials found for Roll No {rollno}."
    
    # Group tutorials by subject
    tutorials_by_subject = {}
    for course in courses:
        subject = course.get("VideoSubject", "Unknown")
        if subject not in tutorials_by_subject:
            tutorials_by_subject[subject] = []
        tutorials_by_subject[subject].append(course)
    
    # Format output
    output = f"Recommended YouTube Tutorials for Roll No {rollno}:\n\n"
    for subject, tutorials in tutorials_by_subject.items():
        output += f"=== {subject} ===\n"
        for idx, tutorial in enumerate(tutorials, 1):
            output += f"{idx}. {tutorial.get('VideoTitle', 'Untitled')}\n"
            output += f"   Author: {tutorial.get('VideoAuthorName', 'Unknown')}\n"
            output += f"   Language: {tutorial.get('VideoLanguage', 'Unknown')}\n"
            output += f"   Link: {tutorial.get('VideoLink', '')}\n\n"
    
    return output

skill_testing_agent = Agent(
    name="skill_testing_agent",
    model=os.getenv('MODEL', 'gemini-2.0-flash'),
    description="Agent to help students select a subject to test after watching YouTube tutorials",
    instruction="""
    You are the Subject Testing Agent for Students.  
    Your job is to let the student select a subject to test and send the selected subject to the root agent.  

    Steps:  
    1. You will receive a `rollno` (roll number) from the root agent. Always start by calling `display_student_tutorials(rollno)` to show the YouTube tutorials grouped by subject.  
    2. From this output, display a clear list of subjects with their tutorial counts.  
    3. Ask the student to choose a subject by name (e.g., "Maths", "Science", "Social").  
    4. Confirm the choice: "You chose <Subject>. Ready to take the test?"  
    5. If yes, return the selected subject name to the root agent.  
    6. If no tutorials are shown, inform the student: "No tutorials found. Please get course recommendations first before taking a test."
    
    Remember:
    - Be friendly and encouraging
    - Students are in Grades 1-10, so keep language simple
    - Show excitement about testing their knowledge!
    """,
    tools=[display_student_tutorials],
    
    )