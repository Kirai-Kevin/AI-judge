# AI-Judge: Dynamic Startup Evaluation System

A flexible, AI-powered platform for comprehensive startup pitch assessments with dynamic ranking and configuration capabilities.

## Table of Contents
- [Features](#features)
- [API Endpoints](#api-endpoints)
  - [Configure Questions](#configure-questions)
  - [Generate Rankings](#generate-rankings)
  - [Download Rankings](#download-rankings)
- [Data Formats](#data-formats)
  - [Question Configuration](#question-configuration)
  - [Startup Evaluation](#startup-evaluation)
  - [Rankings Output](#rankings-output)
- [Setup & Installation](#setup--installation)
- [Running the Server](#running-the-server)
- [Testing](#testing)
- [Error Handling](#error-handling)
- [Security](#security)

## Features

- Dynamic question configuration with weights
- Multi-round evaluation support
- AI-powered feedback analysis
- Comprehensive ranking generation
- CSV/ZIP download functionality
- Flexible data input format
- Nomination and mentorship tracking

## API Endpoints

### Configure Questions

**Endpoint:** `/api/configure-questions`  
**Method:** POST  
**Description:** Configure evaluation criteria and their weights

**Request Body:**
```json
{
  "categories": [
    {
      "name": "Problem",
      "weight": 0.10,
      "questions": [
        {
          "id": "prob_1",
          "text": "Is there a clear problem?",
          "weight": 0.25
        },
        {
          "id": "prob_2",
          "text": "Is there evidence to support the importance of the problem?",
          "weight": 0.25
        }
      ]
    }
  ]
}
```

**Success Response:**
```json
{
  "message": "Questions configuration updated successfully",
  "config": {
    "categories": [
      {
        "name": "Problem",
        "weight": 0.10,
        "questions": [...]
      }
    ]
  }
}
```

### Generate Rankings

**Endpoint:** `/rankings/generate`  
**Method:** POST  
**Description:** Generate comprehensive rankings from startup evaluations

**Request Body:**
```json
[
  {
    "startupId": "startup_123",
    "judgeId": "judge_456",
    "averageScore": 8.5,
    "feedback": "Strong potential in innovation",
    "individualScores": [
      {
        "roundId": "round_1",
        "average": 8.0,
        "criteria": [
          {
            "score": 9,
            "question": "Clear problem identification",
            "skipped": false
          }
        ],
        "feedback": "Good understanding of the market"
      }
    ],
    "isNominated": true,
    "willBeMentored": false,
    "willBeMet": true
  }
]
```

**Success Response:**
```json
{
  "message": "Rankings generated successfully",
  "rankings": [
    {
      "Startup ID": "startup_123",
      "Judge ID": "judge_456",
      "Overall Score": 8.5,
      "Question": "Clear problem identification",
      "Round Average": 8.0,
      "Round Feedback": "Good understanding of the market",
      "Round ID": "round_1",
      "Score": 9,
      "Skipped": false
    }
  ]
}
```

### Download Rankings

**Endpoint:** `/rankings/download`  
**Method:** POST  
**Description:** Generate and download rankings as CSV files in a ZIP archive

**Request Body:** Same as `/rankings/generate` endpoint

**Success Response:**
- Content-Type: application/zip
- File: rankings_[timestamp].zip containing:
  1. `comprehensive_rankings_[timestamp].csv`:
     - Detailed rankings with all criteria scores
     - Round-specific feedback
     - Individual question scores
  2. `summary_rankings_[timestamp].csv`:
     - Overall startup rankings
     - Average scores
     - Nomination status
     - Mentorship/meeting preferences

## Data Formats

### Question Configuration

Questions are organized into categories, each with its own weight:

```json
{
  "categories": [
    {
      "name": "Problem",
      "weight": 0.10,
      "questions": [
        {
          "id": "prob_1",
          "text": "Is there a clear problem?",
          "weight": 0.25
        }
      ]
    }
  ]
}
```

**Field Descriptions:**
- `name`: Category name
- `weight`: Category weight (0-1)
- `questions`: Array of questions
  - `id`: Unique question identifier
  - `text`: Question text
  - `weight`: Question weight within category (0-1)

### Startup Evaluation

Each startup evaluation contains:

```json
{
  "startupId": "unique_identifier",
  "judgeId": "judge_identifier",
  "averageScore": 8.5,
  "feedback": "Overall startup evaluation",
  "individualScores": [
    {
      "roundId": "round_id",
      "average": 8.0,
      "criteria": [
        {
          "score": 9,
          "question": "Evaluation criteria",
          "skipped": false
        }
      ],
      "feedback": "Round-specific feedback"
    }
  ],
  "isNominated": true,
  "willBeMentored": false,
  "willBeMet": true
}
```

**Field Descriptions:**
- `startupId`: Unique identifier for the startup
- `judgeId`: Identifier for the judge
- `averageScore`: Overall score (0-10)
- `feedback`: General feedback
- `individualScores`: Array of round evaluations
  - `roundId`: Round identifier
  - `average`: Round average score
  - `criteria`: Array of criterion evaluations
    - `score`: Score (0-10)
    - `question`: Criterion description
    - `skipped`: If criterion was skipped
  - `feedback`: Round feedback
- `isNominated`: Nomination status
- `willBeMentored`: Mentorship interest
- `willBeMet`: Meeting requested

### Rankings Output

The system generates two types of rankings:

1. **Comprehensive Rankings:**
```csv
Startup ID,Judge ID,Overall Score,Round ID,Round Average,Question,Score,Skipped,Round Feedback
startup_123,judge_456,8.5,round_1,8.0,Clear problem identification,9,false,Good understanding
```

2. **Summary Rankings:**
```csv
Startup ID,Judge ID,Overall Score,Nominated,Mentored,Meeting,Overall Feedback
startup_123,judge_456,8.5,true,false,true,Strong potential in innovation
```

## Setup & Installation

1. Create a `.env` file:
```
GROQ_API_KEY=your_api_key_here
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

The server automatically tries ports 5000, 5001, 5002, 8080, and 8081:

```bash
python app.py
```

## Testing

Run the test script:

```powershell
.\test_endpoints.ps1
```

## Error Handling

The system handles various error cases:

1. **Invalid Input:**
```json
{
  "error": "Missing required field: startupId"
}
```

2. **Server Error:**
```json
{
  "error": "Ranking processor not initialized"
}
```

3. **Processing Error:**
```json
{
  "error": "Error processing rankings: [error details]"
}
```

## Security

- API keys managed via environment variables
- Input validation on all requests
- Secure file handling for downloads
- Error logging without sensitive data
- Temporary file cleanup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
