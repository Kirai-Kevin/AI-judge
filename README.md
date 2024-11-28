# AI-Judge: Startup Evaluation Platform

## Overview
AI-Judge is a comprehensive platform for evaluating and ranking startup pitches using AI-powered analysis and a dynamic scoring system. The platform supports configurable evaluation criteria, making it adaptable to different startup ecosystems and evaluation needs.

## Features
- Dynamic configuration of evaluation criteria and weights
- AI-powered real-time feedback generation
- Flexible scoring system with configurable category weights
- Detailed report generation with scoring breakdowns
- Round-based evaluation support
- Nomination and mentorship tracking

## Configuration
### Question Configuration
Questions are configured dynamically through the API. Here's the structure:

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

### Evaluation Input Format
Each startup evaluation should follow this structure:

```json
{
  "startupId": "unique_id",
  "evaluationConfig": {
    "categories": [
      {
        "name": "Category Name",
        "weight": 0.XX,
        "questions": [
          {
            "id": "question_id",
            "text": "Question text",
            "weight": 0.XX
          }
        ]
      }
    ]
  },
  "evaluations": [
    {
      "roundId": "round_id",
      "responses": [
        {
          "questionId": "question_id",
          "score": 1-10,
          "feedback": "Detailed feedback",
          "skipped": false
        }
      ],
      "roundFeedback": "Overall round feedback"
    }
  ],
  "nominations": {
    "isNominated": boolean,
    "willBeMentored": boolean,
    "willBeMet": boolean
  }
}
```

## API Endpoints

### 1. Question Configuration
**Endpoint:** `/api/configure-questions`
**Method:** POST
- Configure evaluation criteria and weights
- Supports dynamic question management
- Validates configuration structure

### 2. Rankings
**Base Path:** `/rankings`

#### Generate Rankings
**Endpoint:** `/rankings/generate`
**Method:** POST
- Processes startup evaluations
- Generates comprehensive rankings
- Supports round-based evaluation

#### Download Rankings
**Endpoint:** `/rankings/download`
**Method:** GET
- Downloads CSV with rankings
- Includes detailed scores and feedback

### 3. Real-time Feedback
**Base Path:** `/real_time_feedback`

#### Submit Feedback
**Endpoint:** `/real_time_feedback/submit`
**Method:** POST
- Accepts evaluation responses
- Provides immediate AI analysis

### 4. Report Generation
**Base Path:** `/report`

#### Generate Report
**Endpoint:** `/report/generate`
**Method:** POST
- Creates detailed evaluation reports
- Includes AI-powered insights

## Setup
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables in `.env`:
```env
GROQ_API_KEY=your_groq_api_key
```

## Dependencies
- Flask: Web framework
- Groq: AI-powered analysis
- pandas: Data processing
- numpy: Numerical computations
- python-docx: Report generation
- Additional utilities (see requirements.txt)

## Development Status
- Dynamic question configuration 
- Core scoring system 
- AI feedback generation 
- Round-based evaluation 
- Nomination tracking 
- Error handling 

## Best Practices
1. Always configure questions before submitting evaluations
2. Use consistent question IDs across evaluations
3. Ensure category weights sum to 1.0
4. Provide detailed feedback for better AI analysis
5. Regular backup of question configurations

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License
MIT License - See LICENSE file for details
