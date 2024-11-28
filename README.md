# team-tuki

# AI Judge API Documentation

## Overview
This API provides endpoints for an AI-based startup judging system that evaluates and provides feedback for startup pitches and submissions.

## Base URL
When deployed, the API will be accessible at:
https://[your-domain]/api/v1

## Authentication
All requests must include an API key in the header:
Authorization: Bearer YOUR_API_KEY

## Endpoints

### 1. Report Generation
**Endpoint:** `/report/generate_summary`
**Method:** POST

**Request Body:**
```json
{
    "feedback": {
        "high_level": "string",
        "problem": "string",
        "solution": "string",
        "innovation": "string",
        "team": "string",
        "business_model": "string",
        "market_opportunity": "string",
        "technical_feasibility": "string",
        "execution_strategy": "string",
        "communication": "string"
    }
}
```

**Response:**
```json
{
    "summary": "string"    // AI-generated summary of the feedback
}
```

### 2. Real-time Feedback
**Endpoint:** `/real_time_feedback/submit_feedback`
**Method:** POST

**Request Body:**
```json
{
    "feedback": "string"    // Detailed feedback text
}
```

**Response:**
```json
{
    "feedback_analysis": "string"    // AI-generated analysis of strengths and weaknesses
}
```

### 3. Feedback Processor
**Endpoint:** `/feedback_processor/process_feedback`
**Method:** POST

**Request Body:**
```json
{
    "startup_data": {
        "name": "string",
        "description": "string"
    },
    "judge_feedback": [
        {
            "score": "number",
            "comment": "string"
        }
    ]
}
```

**Response:**
```json
{
    "startup_name": "string",
    "analysis": "string",
    "aggregate_scores": ["number"],
    "detailed_feedback": ["string"]
}
```

### 4. Rankings
**Endpoint:** `/rankings/download_rankings`
**Method:** GET

**Query Parameters:**
```json
{
    "comprehensive": "boolean"    // Optional: Get comprehensive rankings
}
```

**Response:**
- Returns a CSV file with startup rankings
- File includes:
  * Startup ID
  * Startup Name
  * Overall Score
  * Category Scores (Problem, Solution, Innovation, etc.)
  * Judge Feedback
  * AI Analysis

## Scoring Categories and Weights
The ranking system uses the following categories and weights:
- Problem (15%)
- Solution (15%)
- Innovation (12%)
- Team (12%)
- Business Model (12%)
- Market Opportunity (12%)
- Technical Feasibility (10%)
- Execution Strategy (7%)
- Communication (5%)

## Error Responses
All endpoints may return the following error responses:

```json
{
    "error": "string",         // Error description
    "status_code": "number"    // HTTP status code
}
```

Common status codes:
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Environment Variables
The following environment variable must be set:
```
GROQ_API_KEY=your_groq_api_key    // Required for AI analysis
```

## Contact
For any technical issues or questions, please contact the development team.