"""Database utilities for the upskilling agent.

This module provides database-related classes and functions for the upskilling agent,
including operations for managing employee data and course recommendations.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from datetime import datetime

from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
DATASET_ID = os.getenv("DATASET_ID", "learning_agent")
TABLE_ID = os.getenv("TABLE_ID", "employees")


class CourseRecommendationDatabase:
    """Handles database operations for course recommendations.
    
    This class provides methods to interact with the BigQuery database
    for managing course recommendations and employee data.
    """
    
    def __init__(self) -> None:
        """Initialize the database client and table reference.
        
        Raises:
            google.auth.exceptions.DefaultCredentialsError: If the default
                credentials cannot be found or are invalid.
        """
        self.client = bigquery.Client(project=PROJECT_ID)
        self.table = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    def get_courses_and_levels_for_employee(self, employee_id: int) -> Dict[str, str]:
        """
        Retrieve recommended courses and their levels for a given employee.
        
        Args:
            employee_id: The ID of the employee
            
        Returns:
            dict: A dictionary mapping course names to their levels
        """
        query = f"""
        SELECT 
            recommended_courses,
            skill_levels
        FROM `{self.table}`
        WHERE EmployeeId = @employee_id
        LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("employee_id", "INT64", employee_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            if results:
                result = results[0]  # Get first row
                try:
                    courses = json.loads(result.recommended_courses)
                    levels = json.loads(result.skill_levels)
                    
                    # Ensure both are lists of the same length
                    if isinstance(courses, list) and isinstance(levels, list) and len(courses) == len(levels):
                        return dict(zip(courses, levels))
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON data for employee {employee_id}: {str(e)}")
            return {}
            
        except Exception as e:
            print(f"Error fetching courses for employee {employee_id}: {str(e)}")
            return {}


class DatabaseSessionService:
    """Service class for managing database sessions and operations.
    
    This class provides a context manager for database operations and handles
    session management for the application. It uses Google BigQuery as the
    underlying database and provides methods for common CRUD operations.
    """
    
    def __init__(self):
        """Initialize the database client and table reference."""
        self.client = bigquery.Client(project=PROJECT_ID)
        self.table = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        self._create_table()

    def _create_table(self):
        """Create the employees table in BigQuery if it doesn't exist."""
        schema = [
            bigquery.SchemaField("EmployeeId", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("Name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("CurrentRole", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("Team", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("CareerGoal", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("TimeAllocated", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("Skills", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("TimeStamp", "TIMESTAMP", mode="NULLABLE")
        ]
        table1 = bigquery.Table(self.table, schema=schema)
        try:
            self.client.create_table(table1)
            print(f"Table {self.table} created.")
        except Exception as e:
            print(f"Table creation skipped or already exists: {e}")

    def employee_exists(self, employee_id: int) -> bool:
        """Check if an employee with the given ID exists in the database.
        
        Args:
            employee_id: The ID of the employee to check
            
        Returns:
            bool: True if the employee exists, False otherwise
        """
        query = f"""
        SELECT 1 FROM `{self.table}` 
        WHERE EmployeeId = @employee_id
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("employee_id", "INT64", employee_id)]
        )
        results = self.client.query(query, job_config=job_config).result()
        return next(results, None) is not None

    def get_employee(self, employee_id: int) -> dict:
        """Retrieve an employee's data by their ID.
        
        Args:
            employee_id: The ID of the employee to retrieve
            
        Returns:
            dict: A dictionary containing the employee's data, or an empty dict if not found
        """
        query = f"""
        SELECT * FROM `{self.table}` 
        WHERE EmployeeId = @employee_id
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("employee_id", "INT64", employee_id)]
        )
        results = list(self.client.query(query, job_config=job_config).result())
        
        if results:
            row = results[0]
            return {
                "EmployeeId": row['EmployeeId'],
                "Name": row['Name'],
                "CurrentRole": row['CurrentRole'],
                "Team": row['Team'],
                "CareerGoal": row['CareerGoal'],
                "TimeAllocated": row['TimeAllocated'],
                "Skills": json.loads(row['Skills']),
                "TimeStamp": str(row['TimeStamp']) if row['TimeStamp'] else None
            }
        return {}

    def insert_employee(self, employee: dict) -> None:
        """Insert a new employee record into the database.
        
        Args:
            employee: A dictionary containing the employee's data
            
        Raises:
            ValueError: If required fields are missing from the employee dictionary
        """
        required_fields = ["EmployeeId", "Name", "CareerGoal"]
        for field in required_fields:
            if field not in employee:
                raise ValueError(f"Missing required field: {field}")
                
        query = f"""
        INSERT INTO `{self.table}` (EmployeeId, Name, CurrentRole, Team, CareerGoal, TimeAllocated, Skills, TimeStamp)
        VALUES (@EmployeeId, @Name, @CurrentRole, @Team, @CareerGoal, @TimeAllocated, @Skills, @TimeStamp)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("EmployeeId", "INT64", employee["EmployeeId"]),
                bigquery.ScalarQueryParameter("Name", "STRING", employee.get("Name", "")),
                bigquery.ScalarQueryParameter("CurrentRole", "STRING", employee.get("CurrentRole")),
                bigquery.ScalarQueryParameter("Team", "STRING", employee.get("Team")),
                bigquery.ScalarQueryParameter("CareerGoal", "STRING", employee.get("CareerGoal", "")),
                bigquery.ScalarQueryParameter("TimeAllocated", "INT64", employee.get("TimeAllocated")),
                bigquery.ScalarQueryParameter("Skills", "STRING", json.dumps(employee.get("Skills", {}))),
                bigquery.ScalarQueryParameter("TimeStamp", "TIMESTAMP", employee.get("TimeStamp", datetime.utcnow().isoformat())),
            ]
        )
        self.client.query(query, job_config=job_config).result()

    def update_employee(self, employee: dict) -> None:
        """Update an existing employee's record in the database.
        
        Args:
            employee: A dictionary containing the updated employee data
            
        Raises:
            ValueError: If the employee ID is not provided or the employee doesn't exist
        """
        if "EmployeeId" not in employee:
            raise ValueError("Employee ID is required for update")
            
        if not self.employee_exists(employee["EmployeeId"]):
            raise ValueError(f"Employee with ID {employee['EmployeeId']} does not exist")
            
        # Fetch existing employee data
        existing = self.get_employee(employee["EmployeeId"])
        
        # Merge existing data with updates
        updated = {
            "EmployeeId": employee["EmployeeId"],
            "Name": employee.get("Name", existing["Name"]),
            "CurrentRole": employee.get("CurrentRole", existing["CurrentRole"]),
            "Team": employee.get("Team", existing["Team"]),
            "CareerGoal": employee.get("CareerGoal", existing["CareerGoal"]),
            "TimeAllocated": employee.get("TimeAllocated", existing["TimeAllocated"]),
            "Skills": employee.get("Skills", existing["Skills"]),
            "TimeStamp": datetime.utcnow().isoformat()
        }
        
        query = f"""
        UPDATE `{self.table}` 
        SET
            Name = @Name,
            CurrentRole = @CurrentRole,
            Team = @Team,
            CareerGoal = @CareerGoal,
            TimeAllocated = @TimeAllocated,
            Skills = @Skills,
            TimeStamp = @TimeStamp
        WHERE EmployeeId = @EmployeeId
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("Name", "STRING", updated["Name"]),
                bigquery.ScalarQueryParameter("CurrentRole", "STRING", updated["CurrentRole"]),
                bigquery.ScalarQueryParameter("Team", "STRING", updated["Team"]),
                bigquery.ScalarQueryParameter("CareerGoal", "STRING", updated["CareerGoal"]),
                bigquery.ScalarQueryParameter("TimeAllocated", "INT64", updated["TimeAllocated"]),
                bigquery.ScalarQueryParameter("Skills", "STRING", json.dumps(updated["Skills"])),
                bigquery.ScalarQueryParameter("TimeStamp", "TIMESTAMP", updated["TimeStamp"]),
                bigquery.ScalarQueryParameter("EmployeeId", "INT64", updated["EmployeeId"]),
            ]
        )
        self.client.query(query, job_config=job_config).result()
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations.
        
        Yields:
            Database session that will be automatically committed or rolled back.
            
        Example:
            with session_scope() as session:
                # perform database operations
                session.query(...)
        """
        try:
            yield self
        except Exception as e:
            print(f"Database error in session_scope: {str(e)}")
            raise


class TeacherDatabase:
    """Handles database operations for teacher profiles and analytics.
    
    This class provides methods to manage teacher profiles, view student data,
    and calculate class averages for subjects.
    """
    
    def __init__(self) -> None:
        """Initialize the database client and create table if not exists."""
        self.client = bigquery.Client(project=PROJECT_ID)
        self.dataset_id = DATASET_ID
        self.table_name = "teachers"
        self.table_id = f"{PROJECT_ID}.{self.dataset_id}.{self.table_name}"
        
        # Create table if it doesn't exist
        self._create_table_if_not_exists()
    
    def _create_table_if_not_exists(self) -> None:
        """Create the teachers table if it doesn't exist."""
        schema = [
            bigquery.SchemaField("StaffID", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("Name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Grades", "STRING", mode="REQUIRED"),  # JSON array as string
            bigquery.SchemaField("Subject", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("TimeStamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        table = bigquery.Table(self.table_id, schema=schema)
        
        try:
            self.client.create_table(table)
            print(f"Created table {self.table_id}")
        except Exception as e:
            # Table likely already exists
            pass
    
    def teacher_exists(self, staff_id: int) -> bool:
        """Check if a teacher exists in the database.
        
        Args:
            staff_id: Teacher's staff ID
            
        Returns:
            True if teacher exists, False otherwise
        """
        query = f"""
            SELECT COUNT(*) as count
            FROM `{self.table_id}`
            WHERE StaffID = @staff_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("staff_id", "INTEGER", staff_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            return results[0]["count"] > 0
        except Exception as e:
            print(f"Error checking teacher existence: {str(e)}")
            return False
    
    def save_teacher(self, staff_id: int, name: str, grades: List[int], subject: str) -> Dict[str, Any]:
        """Save a new teacher profile to the database.
        
        Args:
            staff_id: Teacher's staff ID
            name: Teacher's name
            grades: List of grade levels teacher teaches (e.g., [5, 6, 7])
            subject: Subject teacher teaches
            
        Returns:
            Dictionary with success status and message
        """
        # Convert grades list to JSON string
        grades_json = json.dumps(grades)
        
        row_to_insert = [{
            "StaffID": staff_id,
            "Name": name,
            "Grades": grades_json,
            "Subject": subject,
            "TimeStamp": datetime.now().isoformat()
        }]
        
        try:
            errors = self.client.insert_rows_json(self.table_id, row_to_insert)
            
            if errors:
                return {
                    "success": False,
                    "message": f"Error inserting teacher: {errors}"
                }
            
            return {
                "success": True,
                "message": f"Teacher profile created successfully for {name}!"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error saving teacher: {str(e)}"
            }
    
    def get_teacher(self, staff_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve teacher profile by staff ID.
        
        Args:
            staff_id: Teacher's staff ID
            
        Returns:
            Dictionary with teacher data or None if not found
        """
        query = f"""
            SELECT StaffID, Name, Grades, Subject, TimeStamp
            FROM `{self.table_id}`
            WHERE StaffID = @staff_id
            LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("staff_id", "INTEGER", staff_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                row = results[0]
                return {
                    "staff_id": row["StaffID"],
                    "name": row["Name"],
                    "grades": json.loads(row["Grades"]),  # Convert JSON string back to list
                    "subject": row["Subject"],
                    "timestamp": row["TimeStamp"].isoformat() if row["TimeStamp"] else None
                }
            return None
        except Exception as e:
            print(f"Error getting teacher: {str(e)}")
            return None
    
    def update_teacher(self, staff_id: int, name: str = None, grades: List[int] = None, subject: str = None) -> Dict[str, Any]:
        """Update teacher profile.
        
        Args:
            staff_id: Teacher's staff ID
            name: Updated name (optional)
            grades: Updated grades list (optional)
            subject: Updated subject (optional)
            
        Returns:
            Dictionary with success status and message
        """
        # Build update query dynamically based on provided fields
        updates = []
        params = [bigquery.ScalarQueryParameter("staff_id", "INTEGER", staff_id)]
        
        if name:
            updates.append("Name = @name")
            params.append(bigquery.ScalarQueryParameter("name", "STRING", name))
        
        if grades:
            grades_json = json.dumps(grades)
            updates.append("Grades = @grades")
            params.append(bigquery.ScalarQueryParameter("grades", "STRING", grades_json))
        
        if subject:
            updates.append("Subject = @subject")
            params.append(bigquery.ScalarQueryParameter("subject", "STRING", subject))
        
        if not updates:
            return {
                "success": False,
                "message": "No fields to update"
            }
        
        updates.append("TimeStamp = CURRENT_TIMESTAMP()")
        
        query = f"""
            UPDATE `{self.table_id}`
            SET {', '.join(updates)}
            WHERE StaffID = @staff_id
        """
        
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()  # Wait for query to complete
            
            return {
                "success": True,
                "message": "Teacher profile updated successfully!"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating teacher: {str(e)}"
            }
    
    def get_class_average(self, grade: int, subject: str) -> Dict[str, Any]:
        """Calculate class average for a specific grade and subject.
        
        Args:
            grade: Grade level (1-10)
            subject: Subject name (Maths, Science, Social, Language1, Language2, Language3)
            
        Returns:
            Dictionary with class average and student count
        """
        # Map subject names to database columns
        subject_column_map = {
            "Maths": "Maths",
            "Science": "Science",
            "Social": "Social",
            "Language1": "Language1",
            "Language2": "Language2",
            "Language3": "Language3"
        }
        
        column_name = subject_column_map.get(subject)
        if not column_name:
            return {
                "success": False,
                "message": f"Invalid subject: {subject}"
            }
        
        # Query students table for class average
        student_table_id = f"{PROJECT_ID}.{self.dataset_id}.students"
        
        query = f"""
            SELECT 
                AVG({column_name}) as average_score,
                COUNT(*) as student_count,
                MIN({column_name}) as min_score,
                MAX({column_name}) as max_score
            FROM `{student_table_id}`
            WHERE Grade = @grade
            AND {column_name} IS NOT NULL
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("grade", "INTEGER", grade)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results and results[0]["student_count"] > 0:
                row = results[0]
                return {
                    "success": True,
                    "grade": grade,
                    "subject": subject,
                    "average_score": round(row["average_score"], 2) if row["average_score"] else 0,
                    "student_count": row["student_count"],
                    "min_score": row["min_score"],
                    "max_score": row["max_score"]
                }
            else:
                return {
                    "success": False,
                    "message": f"No students found for Grade {grade}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error calculating class average: {str(e)}"
            }


class StudentDatabase:
    """Handles database operations for student profiles.
    
    This class provides methods to interact with the BigQuery database
    for managing student data including grades, scores, and language preferences.
    """
    
    def __init__(self) -> None:
        """Initialize the database client and table reference."""
        self.client = bigquery.Client(project=PROJECT_ID)
        self.table = f"{PROJECT_ID}.{DATASET_ID}.students"
        self._create_table()
    
    def _create_table(self):
        """Create the students table in BigQuery if it doesn't exist."""
        schema = [
            bigquery.SchemaField("RollNo", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("Name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Grade", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("Language", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Language1", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("Language2", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("Language3", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("Maths", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("Science", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("Social", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("TimeStamp", "TIMESTAMP", mode="NULLABLE")
        ]
        table = bigquery.Table(self.table, schema=schema)
        try:
            self.client.create_table(table)
            print(f"Table {self.table} created.")
        except Exception as e:
            print(f"Table creation skipped or already exists: {e}")
    
    def student_exists(self, rollno: int) -> bool:
        """Check if a student with the given roll number exists in the database.
        
        Args:
            rollno: The roll number of the student to check
            
        Returns:
            bool: True if the student exists, False otherwise
        """
        query = f"""
        SELECT 1 FROM `{self.table}` 
        WHERE RollNo = @rollno
        LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("rollno", "INT64", rollno)]
        )
        results = self.client.query(query, job_config=job_config).result()
        return next(results, None) is not None
    
    def get_student(self, rollno: int) -> dict:
        """Retrieve a student's data by their roll number.
        
        Args:
            rollno: The roll number of the student to retrieve
            
        Returns:
            dict: A dictionary containing the student's data, or an empty dict if not found
        """
        query = f"""
        SELECT * FROM `{self.table}` 
        WHERE RollNo = @rollno
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("rollno", "INT64", rollno)]
        )
        results = list(self.client.query(query, job_config=job_config).result())
        
        if results:
            row = results[0]
            return {
                "RollNo": row['RollNo'],
                "Name": row['Name'],
                "Grade": row['Grade'],
                "Language": row['Language'],
                "Language1": row.get('Language1', 0),
                "Language2": row.get('Language2', 0),
                "Language3": row.get('Language3', 0),
                "Maths": row.get('Maths', 0),
                "Science": row.get('Science', 0),
                "Social": row.get('Social', 0),
                "TimeStamp": str(row['TimeStamp']) if row.get('TimeStamp') else None
            }
        return {}
    
    def insert_student(self, student: dict) -> None:
        """Insert a new student record into the database.
        
        Args:
            student: A dictionary containing the student's data
            
        Raises:
            ValueError: If required fields are missing from the student dictionary
        """
        required_fields = ["RollNo", "Name", "Grade", "Language"]
        for field in required_fields:
            if field not in student:
                raise ValueError(f"Missing required field: {field}")
                
        query = f"""
        INSERT INTO `{self.table}` 
        (RollNo, Name, Grade, Language, Language1, Language2, Language3, Maths, Science, Social, TimeStamp)
        VALUES (@RollNo, @Name, @Grade, @Language, @Language1, @Language2, @Language3, @Maths, @Science, @Social, @TimeStamp)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("RollNo", "INT64", student["RollNo"]),
                bigquery.ScalarQueryParameter("Name", "STRING", student.get("Name", "")),
                bigquery.ScalarQueryParameter("Grade", "INT64", student.get("Grade", 1)),
                bigquery.ScalarQueryParameter("Language", "STRING", student.get("Language", "English")),
                bigquery.ScalarQueryParameter("Language1", "INT64", student.get("Language1", 0)),
                bigquery.ScalarQueryParameter("Language2", "INT64", student.get("Language2", 0)),
                bigquery.ScalarQueryParameter("Language3", "INT64", student.get("Language3", 0)),
                bigquery.ScalarQueryParameter("Maths", "INT64", student.get("Maths", 0)),
                bigquery.ScalarQueryParameter("Science", "INT64", student.get("Science", 0)),
                bigquery.ScalarQueryParameter("Social", "INT64", student.get("Social", 0)),
                bigquery.ScalarQueryParameter("TimeStamp", "TIMESTAMP", student.get("TimeStamp", datetime.utcnow().isoformat())),
            ]
        )
        self.client.query(query, job_config=job_config).result()
    
    def update_student(self, student: dict) -> None:
        """Update an existing student's record in the database.
        
        Args:
            student: A dictionary containing the updated student data
            
        Raises:
            ValueError: If the roll number is not provided or the student doesn't exist
        """
        if "RollNo" not in student:
            raise ValueError("Roll number is required for update")
            
        if not self.student_exists(student["RollNo"]):
            raise ValueError(f"Student with Roll No {student['RollNo']} does not exist")
            
        # Fetch existing student data
        existing = self.get_student(student["RollNo"])
        
        # Merge existing data with updates
        updated = {
            "RollNo": student["RollNo"],
            "Name": student.get("Name", existing["Name"]),
            "Grade": student.get("Grade", existing["Grade"]),
            "Language": student.get("Language", existing["Language"]),
            "Language1": student.get("Language1", existing["Language1"]),
            "Language2": student.get("Language2", existing["Language2"]),
            "Language3": student.get("Language3", existing["Language3"]),
            "Maths": student.get("Maths", existing["Maths"]),
            "Science": student.get("Science", existing["Science"]),
            "Social": student.get("Social", existing["Social"]),
            "TimeStamp": datetime.utcnow().isoformat()
        }
        
        query = f"""
        UPDATE `{self.table}` 
        SET
            Name = @Name,
            Grade = @Grade,
            Language = @Language,
            Language1 = @Language1,
            Language2 = @Language2,
            Language3 = @Language3,
            Maths = @Maths,
            Science = @Science,
            Social = @Social,
            TimeStamp = @TimeStamp
        WHERE RollNo = @RollNo
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("Name", "STRING", updated["Name"]),
                bigquery.ScalarQueryParameter("Grade", "INT64", updated["Grade"]),
                bigquery.ScalarQueryParameter("Language", "STRING", updated["Language"]),
                bigquery.ScalarQueryParameter("Language1", "INT64", updated["Language1"]),
                bigquery.ScalarQueryParameter("Language2", "INT64", updated["Language2"]),
                bigquery.ScalarQueryParameter("Language3", "INT64", updated["Language3"]),
                bigquery.ScalarQueryParameter("Maths", "INT64", updated["Maths"]),
                bigquery.ScalarQueryParameter("Science", "INT64", updated["Science"]),
                bigquery.ScalarQueryParameter("Social", "INT64", updated["Social"]),
                bigquery.ScalarQueryParameter("TimeStamp", "TIMESTAMP", updated["TimeStamp"]),
                bigquery.ScalarQueryParameter("RollNo", "INT64", updated["RollNo"]),
            ]
        )
        self.client.query(query, job_config=job_config).result()
    
    def get_weak_subjects(self, rollno: int, threshold: int = 60) -> list:
        """Get list of subjects where student is scoring below threshold.
        
        Args:
            rollno: Student's roll number
            threshold: Score below which subject is considered weak (default: 60)
            
        Returns:
            list: List of subject names where score < threshold
        """
        student = self.get_student(rollno)
        if not student:
            return []
        
        weak_subjects = []
        subjects = {
            "Language1": student.get("Language1", 0),
            "Language2": student.get("Language2", 0),
            "Language3": student.get("Language3", 0),
            "Maths": student.get("Maths", 0),
            "Science": student.get("Science", 0),
            "Social": student.get("Social", 0)
        }
        
        for subject, score in subjects.items():
            if score > 0 and score < threshold:
                weak_subjects.append(subject)
        
        return weak_subjects


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


class StudentTestResultsDatabase:
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
