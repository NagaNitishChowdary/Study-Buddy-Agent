from google.cloud import bigquery
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
DATASET_ID = os.getenv("DATASET_ID", "learning_agent")


class StudentCourseRecommendationDatabase:
    """Handles database operations for YouTube course recommendations.
    
    This class provides methods to store and retrieve YouTube tutorial
   recommendations for students.
    """
    
    def __init__(self) -> None:
        """Initialize the database client and table reference."""
        self.client = bigquery.Client(project=PROJECT_ID)
        self.table = f"{PROJECT_ID}.{DATASET_ID}.student_course_recommendations"
        self._create_table()
    
    def _create_table(self):
        """Create the student course recommendations table if it doesn't exist."""
        schema = [
            bigquery.SchemaField("RollNo", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("StudentName", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("VideoAuthorName", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("VideoLink", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("VideoLanguage", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("VideoSubject", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("VideoTitle", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("VideoDescription", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("TimeStamp", "TIMESTAMP", mode="NULLABLE")
        ]
        table = bigquery.Table(self.table, schema=schema)
        try:
            self.client.create_table(table)
            print(f"Table {self.table} created.")
        except Exception as e:
            print(f"Table creation skipped or already exists: {e}")
    
    def insert_recommendation(self, course: dict) -> None:
        """Insert a course recommendation into the database.
        
        Args:
            course: Dictionary containing course details
                Required keys: RollNo, StudentName, VideoAuthorName, VideoLink,
                VideoLanguage, VideoSubject, VideoTitle
        """
        query = f"""
        INSERT INTO `{self.table}` 
        (RollNo, StudentName, VideoAuthorName, VideoLink, VideoLanguage, VideoSubject, VideoTitle, VideoDescription, TimeStamp)
        VALUES (@RollNo, @StudentName, @VideoAuthorName, @VideoLink, @VideoLanguage, @VideoSubject, @VideoTitle, @VideoDescription, @TimeStamp)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("RollNo", "INT64", course["RollNo"]),
                bigquery.ScalarQueryParameter("StudentName", "STRING", course.get("StudentName", "")),
                bigquery.ScalarQueryParameter("VideoAuthorName", "STRING", course.get("VideoAuthorName", "Unknown")),
                bigquery.ScalarQueryParameter("VideoLink", "STRING", course.get("VideoLink", "")),
                bigquery.ScalarQueryParameter("VideoLanguage", "STRING", course.get("VideoLanguage", "English")),
                bigquery.ScalarQueryParameter("VideoSubject", "STRING", course.get("VideoSubject", "")),
                bigquery.ScalarQueryParameter("VideoTitle", "STRING", course.get("VideoTitle", "")),
                bigquery.ScalarQueryParameter("VideoDescription", "STRING", course.get("VideoDescription", "")),
                bigquery.ScalarQueryParameter("TimeStamp", "TIMESTAMP", datetime.utcnow().isoformat()),
            ]
        )
        self.client.query(query, job_config=job_config).result()
    
    def get_courses_for_student(self, rollno: int) -> list:
        """Retrieve all course recommendations for a student.
        
        Args:
            rollno: Student's roll number
            
        Returns:
            list: List of course dictionaries
        """
        query = f"""
        SELECT * FROM `{self.table}` 
        WHERE RollNo = @rollno
        ORDER BY VideoSubject, TimeStamp DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("rollno", "INT64", rollno)]
        )
        results = self.client.query(query, job_config=job_config).result()
        
        courses = []
        for row in results:
            courses.append({
                "RollNo": row['RollNo'],
                "StudentName": row['StudentName'],
                "VideoAuthorName": row['VideoAuthorName'],
                "VideoLink": row['VideoLink'],
                "VideoLanguage": row['VideoLanguage'],
                "VideoSubject": row['VideoSubject'],
                "VideoTitle": row['VideoTitle'],
                "VideoDescription": row.get('VideoDescription', ''),
                "TimeStamp": str(row['TimeStamp']) if row.get('TimeStamp') else None
            })
        return courses
    
    def get_courses_by_subject(self, rollno: int, subject: str) -> list:
        """Retrieve course recommendations for a specific subject.
        
        Args:
            rollno: Student's roll number
            subject: Subject name (e.g., "Maths", "Science")
            
        Returns:
            list: List of course dictionaries for the subject
        """
        query = f"""
        SELECT * FROM `{self.table}` 
        WHERE RollNo = @rollno AND VideoSubject = @subject
        ORDER BY TimeStamp DESC
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("rollno", "INT64", rollno),
                bigquery.ScalarQueryParameter("subject", "STRING", subject)
            ]
        )
        results = self.client.query(query, job_config=job_config).result()
        
        courses = []
        for row in results:
            courses.append({
                "RollNo": row['RollNo'],
                "StudentName": row['StudentName'],
                "VideoAuthorName": row['VideoAuthorName'],
                "VideoLink": row['VideoLink'],
                "VideoLanguage": row['VideoLanguage'],
                "VideoSubject": row['VideoSubject'],
                "VideoTitle": row['VideoTitle'],
                "VideoDescription": row.get('VideoDescription', ''),
                "TimeStamp": str(row['TimeStamp']) if row.get('TimeStamp') else None
            })
        return courses
    
    def delete_student_courses(self, rollno: int) -> None:
        """Delete all course recommendations for a student.
        
        Args:
            rollno: Student's roll number
        """
        query = f"""
        DELETE FROM `{self.table}` 
        WHERE RollNo = @rollno
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("rollno", "INT64", rollno)]
        )
        self.client.query(query, job_config=job_config).result()