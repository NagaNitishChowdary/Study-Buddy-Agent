# Study Buddy Agent: AI Tutors for Foundational Learning

**Study Buddy Agent** is an AI-powered tutoring system designed to support students in government schools across India. It provides personalized assistance in foundational literacy and numeracy, adapts to each learner's pace, and offers multilingual support. The system also empowers teachers with insights into student performance and class averages.

## 🚀 Features

### For Students (Study Buddy)
*   **Personalized Profile**: Tracks student details, grade, language preference, and subject scores.
*   **Smart Recommendations**: Automatically identifies weak subjects (Score < 60) and recommends curated video courses.
    *   **Bilingual Support**: Provides two video links per weak subject: one in **English** and one in the student's **Native Language**.
    *   **Robust Validation**: Ensures all video links are valid and accessible.
*   **Skill Testing**: Generates subject-specific questions to test understanding and provides instant feedback.

### For Teachers (Teacher Agent)
*   **Profile Management**: Allows teachers to register and manage their profiles (Subjects, Grades taught).
*   **Student Insights**: View individual student profiles and performance data.
*   **Class Analytics**: Calculate and view class averages for specific subjects to identify learning gaps.

## 🏗️ Architecture

The system is built using **Google Agent Development Kit (ADK)** and **Gemini Models**, with **BigQuery** as the backend database.

*   **Root Agent**: Acts as a central router, directing users to the appropriate flow based on their role (Student or Teacher).
*   **Study Buddy Agent**: Orchestrates student workflows (Profile -> Recommendations -> Testing).
    *   `video_course_recommendation_agent`: Generates video links.
    *   `student_course_validation_agent`: Validates links.
    *   `student_skill_testing_agent`: Manages quizzes.
*   **Teacher Agent**: Orchestrates teacher workflows (Profile -> Analytics).
*   **Database**: BigQuery tables for `student`, `teacher`, and `student_recommendations`.

## 🛠️ Setup & Installation

### Prerequisites
*   Python 3.10+
*   Google Cloud Project with BigQuery API enabled.
*   Google Cloud Service Account with BigQuery Data Editor/Owner permissions.

### Installation

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd study-buddy-agent
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration**
    Create a `.env` file in the `app/app` directory with the following variables:
    ```env
    GOOGLE_CLOUD_PROJECT=your-project-id
    DATASET_ID=study_buddy_agent
    MODEL=gemini-2.0-flash
    # Ensure GOOGLE_APPLICATION_CREDENTIALS is set in your environment or logged in via gcloud
    ```

4.  **Run the Agent**
    You can run the agent using the ADK CLI:
    ```bash
    cd app
    adk web
    ```

## 🧪 Verification

A verification script `verify_study_buddy.py` is included to test the core logic without needing a live database connection (mocks BigQuery).

```bash
python verify_study_buddy.py
```

## 📂 Project Structure

```
.
├── app/
│   ├── app/
│   │   ├── agent.py              # Root Agent (Router)
│   │   ├── db_utils.py           # Database Services (Student & Teacher)
│   │   ├── subagents/
│   │   │   ├── study_buddy/      # Student Agent & Subagents
│   │   │   └── teacher/          # Teacher Agent
│   │   └── ...
├── verify_study_buddy.py         # Verification Script
└── requirements.txt              # Dependencies
```

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements.
