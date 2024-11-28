# AI-Judge: Startup Evaluation Platform

## Overview
AI-Judge is a comprehensive platform for evaluating and ranking startup pitches using AI-powered analysis and a detailed scoring system.

## Features
- Automated startup evaluation across 9 key categories
- AI-powered real-time feedback generation
- Comprehensive scoring system with weighted categories
- Detailed report generation with scoring breakdowns
- Structured input format for consistent evaluations

## Input Format
Each startup evaluation should include feedback for the following categories:

1. Problem (10%)
   - Clear problem identification
   - Evidence of importance
   - Problem solvability
   - Team's problem obsession

2. Solution (10%)
   - Solution coherence
   - Clear vision
   - Technical feasibility

3. Innovation (10%)
   - AI application novelty
   - Unique problem-solving approach

4. Team (20%)
   - Skills and expertise
   - Leadership quality
   - Team dynamics
   - Agility and adaptability

5. Business Model (10%)
   - Revenue model viability
   - Business model clarity

6. Market Opportunity (10%)
   - Market size assessment
   - Growth potential
   - Competition analysis

7. Technical Feasibility (10%)
   - Technical implementation viability
   - Resource requirements

8. Execution Strategy (10%)
   - Implementation plan
   - Risk management

9. Communication (10%)
   - Pitch clarity
   - Presentation quality
   - Response effectiveness

## Setup
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables in `.env`:
```
GROQ_API_KEY=your_groq_api_key
```

## API Endpoints

### 1. Rankings Endpoints
**Base Path:** `/rankings`

#### Generate Rankings
**Endpoint:** `/rankings/generate`
**Method:** POST
```json
{
    "startup_name": "string",
    "evaluations": {
        "problem": {
            "clear_problem": 1-10,
            "evidence": 1-10,
            "solvability": 1-10,
            "team_obsession": 1-10
        },
        "solution": {
            "coherence": 1-10,
            "vision": 1-10,
            "feasibility": 1-10
        },
        // ... similar format for other categories
    }
}
```

#### Download Rankings
**Endpoint:** `/rankings/download`
**Method:** GET
Downloads a CSV file containing all startup rankings and scores

### 2. Real-time Feedback Endpoints
**Base Path:** `/real_time_feedback`

#### Submit Feedback
**Endpoint:** `/real_time_feedback/submit`
**Method:** POST
```json
{
    "startup_name": "string",
    "feedback_text": "string",
    "category": "string"  // One of: problem, solution, innovation, etc.
}
```

#### Get Real-time Analysis
**Endpoint:** `/real_time_feedback/analyze`
**Method:** POST
```json
{
    "feedback": "string",
    "context": "string"  // Optional additional context
}
```

### 3. Report Endpoints
**Base Path:** `/report`

#### Generate Report
**Endpoint:** `/report/generate`
**Method:** POST
```json
{
    "startup_name": "string",
    "feedback_data": {
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

#### Generate Summary
**Endpoint:** `/report/generate_summary`
**Method:** POST
```json
{
    "feedback": {
        "high_level": "string",
        "detailed_feedback": {
            "strengths": ["string"],
            "weaknesses": ["string"],
            "recommendations": ["string"]
        }
    }
}
```

### 4. Feedback Processor Endpoints
**Base Path:** `/feedback_processor`

#### Process Feedback
**Endpoint:** `/feedback_processor/process`
**Method:** POST
```json
{
    "startup_data": {
        "name": "string",
        "pitch_text": "string"
    },
    "feedback_items": [{
        "category": "string",
        "score": number,
        "comments": "string"
    }]
}
```

#### Aggregate Feedback
**Endpoint:** `/feedback_processor/aggregate`
**Method:** POST
```json
{
    "startup_id": "string",
    "feedback_entries": [{
        "judge_id": "string",
        "scores": {
            "category": number
        },
        "comments": "string"
    }]
}
```

## Dependencies
- Flask: Web framework
- Groq: AI-powered analysis
- pandas: Data processing
- python-docx: Report generation
- numpy: Numerical computations
- Additional utilities (see requirements.txt)

## Development Status
- Core scoring system implemented
- AI feedback generation
- Basic API endpoints
- Testing suite
- Error handling improvements

## Contributing
Contributions are welcome! Please follow the standard pull request process.
