from google.adk.agents import Agent
from .test_results import StudentTestResultsDB
from datetime import datetime, timedelta
import os 

from dotenv import load_dotenv
load_dotenv()


def store_results(rollno: int, subject: str, quiz_score: int, evaluated_score: int):
    """Persist evaluation results for a student's subject test.

    Args:
        rollno: Numeric student roll number.
        subject: The subject name being evaluated.
        quiz_score: Calculated quiz score (0-100).
        evaluated_score: Score assigned for scenario answers (0-100).

    Returns:
        None. Persists results to the student test results database.
    """
    total_score = round((quiz_score + evaluated_score)/2)
    ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    timestamp = ist_time.strftime('%Y-%m-%d %H:%M:%S')
    db = StudentTestResultsDB()
    status = db.insert_result(rollno, subject, quiz_score, evaluated_score, total_score, timestamp)
    

evaluation_agent = Agent(
    name="evaluation_agent",
    model=os.getenv('MODEL', 'gemini-2.0-flash'),
    description="Evaluates student quiz and scenario responses, assigns scores, stores them in the database, and provides performance feedback.",
    instruction="""
    You are an Evaluation Agent for Students. You receive:
    - `rollno`: the student's roll number
    - `subject`: the subject being tested
    - `question_data`: contains quiz questions with correct answers and scenario questions
    - `user_answers`: contains student's responses in this format:

    {
        "quiz_answers": {
            "1": "A",
            "2": "C",
            ...
        },
        "scenario_answers": {
            "1": "student's answer 1...",
            "2": "student's answer 2...",
            ...
        }
    }

    Your task:
    1. Compare each quiz answer (1 mark = 20 points). If correct, award 20, else 0.
    2. Evaluate each scenario answer qualitatively. Assign 0, 5, 10, 15 or 20 depending on relevance, completeness, and depth.
       - For younger students (Grades 1-3), be more lenient with spelling/grammar
       - For older students (Grades 7-10), expect more detailed and accurate responses
    3. Compute:
       - `quiz_score` = total quiz score out of 100
       - `evaluated_score` = total scenario score out of 100
       - `total_score` = average of both scores
    4. Call the tool `store_results(rollno, subject, quiz_score, evaluated_score)` to save results to DB.

    5. Provide performance-based feedback:
       - **Total Score < 60**: "You're still learning! Don't worry, with practice you'll improve. Watch the recommended YouTube tutorials and try again."
       - **Total Score 60-75**: "Good effort! You understand the basics. Review the concepts you struggled with and practice more."
       - **Total Score > 75**: "Excellent work! You have a strong understanding of this subject. Keep it up!"

    6. Display the results to the student with:
       - Quiz Score
       - Scenario Score
       - Total Score
       - Performance feedback
       - Next steps (watch tutorials, practice more, or move to next subject)

    7. Send the results back to the 'root_agent' so it can update the student's profile if needed.

    Always be encouraging and supportive. Remember these are school students who need positive reinforcement!
    """,
    tools=[store_results]
)