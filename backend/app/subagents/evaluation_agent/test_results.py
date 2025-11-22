from google.cloud import bigquery
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
DATASET_ID = os.getenv("DATASET_ID", "learning_agent")


class StudentTestResultsDB:
    """Handles database operations for student test results.
    
    This class provides methods to store and retrieve test performance data.
    """
    
    def __init__(self) -> None:
        """Initialize the database client and table reference."""
        self.client = bigquery.Client(project=PROJECT_ID)
        self.table = f"{PROJECT_ID}.{DATASET_ID}.student_test_results"
        self._create_table()
    
    def _create_table(self):
        """Create the student test results table if it doesn't exist."""
        schema = [
            bigquery.SchemaField("RollNo", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("Subject", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("QuizScore", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("EvaluatedScore", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("TotalScore", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("TestDate", "TIMESTAMP", mode="REQUIRED")
        ]
        table = bigquery.Table(self.table, schema=schema)
        try:
            self.client.create_table(table)
            print(f"Table {self.table} created.")
        except Exception as e:
            print(f"Table creation skipped or already exists: {e}")
    
    def insert_result(self, rollno: int, subject: str, quiz_score: int, 
                     evaluated_score: int, total_score: int, timestamp: str) -> None:
        """Insert a test result into the database.
        
        Args:
            rollno: Student's roll number
            subject: Subject tested
            quiz_score: Score on multiple choice questions (0-100)
            evaluated_score: Score on descriptive questions (0-100)
            total_score: Average of both scores
            timestamp: When test was taken (ISO format string)
        """
        query = f"""
        INSERT INTO `{self.table}` 
        (RollNo, Subject, QuizScore, EvaluatedScore, TotalScore, TestDate)
        VALUES (@RollNo, @Subject, @QuizScore, @EvaluatedScore, @TotalScore, @TestDate)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("RollNo", "INT64", rollno),
                bigquery.ScalarQueryParameter("Subject", "STRING", subject),
                bigquery.ScalarQueryParameter("QuizScore", "INT64", quiz_score),
                bigquery.ScalarQueryParameter("EvaluatedScore", "INT64", evaluated_score),
                bigquery.ScalarQueryParameter("TotalScore", "INT64", total_score),
                bigquery.ScalarQueryParameter("TestDate", "TIMESTAMP", timestamp),
            ]
        )
        self.client.query(query, job_config=job_config).result()
    
    def get_student_results(self, rollno: int) -> list:
        """Retrieve all test results for a student.
        
        Args:
            rollno: Student's roll number
            
        Returns:
            list: List of result dictionaries
        """
        query = f"""
        SELECT * FROM `{self.table}` 
        WHERE RollNo = @rollno
        ORDER BY TestDate DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("rollno", "INT64", rollno)]
        )
        results = self.client.query(query, job_config=job_config).result()
        
        test_results = []
        for row in results:
            test_results.append({
                "RollNo": row['RollNo'],
                "Subject": row['Subject'],
                "QuizScore": row['QuizScore'],
                "EvaluatedScore": row['EvaluatedScore'],
                "TotalScore": row['TotalScore'],
                "TestDate": str(row['TestDate']) if row.get('TestDate') else None
            })
        return test_results
    
    def get_subject_performance(self, rollno: int, subject: str) -> list:
        """Retrieve test results for a specific subject.
        
        Args:
            rollno: Student's roll number
            subject: Subject name
            
        Returns:
            list: List of result dictionaries for the subject
        """
        query = f"""
        SELECT * FROM `{self.table}` 
        WHERE RollNo = @rollno AND Subject = @subject
        ORDER BY TestDate DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("rollno", "INT64", rollno),
                bigquery.ScalarQueryParameter("subject", "STRING", subject)
            ]
        )
        results = self.client.query(query, job_config=job_config).result()
        
        test_results = []
        for row in results:
            test_results.append({
                "RollNo": row['RollNo'],
                "Subject": row['Subject'],
                "QuizScore": row['QuizScore'],
                "EvaluatedScore": row['EvaluatedScore'],
                "TotalScore": row['TotalScore'],
                "TestDate": str(row['TestDate']) if row.get('TestDate') else None
            })
        return test_results