# {{ DOCUMENT_TITLE }}

**Base URL:** [https://ai-judge-3.onrender.com](https://ai-judge-3.onrender.com)

## Overview
The AI-Judge application is designed to evaluate startup pitches and provide feedback in a structured format. The backend is built using Flask, and it offers various endpoints for generating feedback, downloading CSV reports, and serving a simple download page.

## API Endpoints

### 1. **Submit Feedback**
- **Endpoint:** `/api/submit_feedback`
- **Method:** `POST`
- **Description:** This endpoint accepts feedback data for a startup pitch and generates a summary and a CSV report.
- **Request Body:**
  ```json
  {
    "scoringTime": "2023-07-20T15:30:00Z",
    "totalScore": 85,
    "meetStartup": true,
    "mentorStartup": false,
    "nominateNextRound": true,
    "overallFeedback": "Strong potential with innovative solution",
    "judgeId": "507f1f77bcf86cd799439011",
    "startupId": "507f1f77bcf86cd799439012",
    "roundId": "507f1f77bcf86cd799439013",
    "sectionScores": {
      "teamSection": {
        "rawAverage": 4.5,
        "percentageScore": 90,
        "weightedScore": 27,
        "maxPoints": 30,
        "feedback": "Experienced leadership team",
        "isSkipped": false,
        "individualScores": {
          "leadership": 5,
          "experience": 4
        },
        "totalPossibleQuestions": 2,
        "answeredQuestions": 2
      }
    },
    "rawFormData": {
      "teamSection": {
        "scores": {
          "leadership": 5,
          "experience": 4
        },
        "feedback": "Strong team composition",
        "isSkipped": false
      }
    }
  }
  ```
- **Response:**
  - **Success (200):** Returns a CSV file containing the feedback summary.
  - **Error (400):** Returns an error message if no data is provided or if there is an issue processing the feedback.

### 2. **Download Feedback CSV**
- **Endpoint:** `/download_feedback_csv/<pitch_id>`
- **Method:** `GET`
- **Description:** This endpoint generates a downloadable CSV file containing feedback for a specific pitch identified by `pitch_id`.
- **Response:**
  - **Success (200):** Returns a CSV file with the pitch evaluation summary.
  - **Error (404):** Returns an error message if no data is found for the given pitch ID.

### 3. **Download Page**
- **Endpoint:** `/download_page/<pitch_id>`
- **Method:** `GET`
- **Description:** Serves a simple HTML page with a download button for the feedback CSV.
- **Response:**
  - **Success (200):** Returns an HTML page with a download link for the CSV file.

## Configuration
- **Environment Variables:**
  - `DOCUMENT_TITLE`: Set this to customize the title of the feedback document.
  - `LOGGING_LEVEL`: Set this to adjust the logging level (e.g., DEBUG, INFO, WARNING).

## How the Code Works

### Key Functions
- **[generate_summary(data)](cci:1://file:///home/michael/Desktop/AI-judge/app.py:148:0-197:13)**: This function takes the feedback data as input and generates a structured summary using AI analysis.
- **[calculate_overall_score(data)](cci:1://file:///home/michael/Desktop/AI-judge/app.py:240:0-263:36)**: This function computes the overall score based on the provided scoring sections in the feedback data.
- **[get_pitch_data(pitch_id)](cci:1://file:///home/michael/Desktop/AI-judge/app.py:438:0-449:8)**: This helper function retrieves the pitch data from the storage system based on the provided pitch ID.

### Workflow
1. **Feedback Submission**: When feedback is submitted through the `/api/submit_feedback` endpoint, the application processes the data, generates a summary, calculates scores, and prepares the data for CSV output.
2. **CSV Generation**: The application creates a CSV file in memory, writing metadata, scoring sections, and general feedback into it.
3. **CSV Download**: The `/download_feedback_csv/<pitch_id>` endpoint allows users to download the generated CSV file for a specific pitch.
4. **Download Page**: The `/download_page/<pitch_id>` endpoint serves a simple HTML page with a link to download the feedback CSV.

### Logging
The application uses logging to track errors and debug information, making it easier to troubleshoot issues during the feedback processing.
