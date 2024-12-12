import os
import logging
from flask import Flask, request, jsonify, send_file
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import random
from groq import AsyncGroq, Groq
from functools import wraps
from dotenv import load_dotenv
import time
from datetime import datetime
import io
from report import report_bp, generate_feedback_summary
from real_time_feedback import real_time_feedback_bp
from feedback_processor import feedback_processor_bp
from rankings import rankings_bp, init_ranking_processor
from flask_cors import CORS
import csv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(rankings_bp, url_prefix='/rankings')
app.register_blueprint(report_bp, url_prefix='/report')
app.register_blueprint(real_time_feedback_bp, url_prefix='/real_time_feedback')
app.register_blueprint(feedback_processor_bp, url_prefix='/feedback_processor')

# Initialize the ranking processor
init_ranking_processor(api_key=os.getenv('GROQ_API_KEY'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def create_feedback_document(data, summary):
    """
    Create a professionally formatted Word document with the feedback.
    """
    doc = Document()
    
    # Document title
    title = doc.add_heading('Pitch Feedback Report', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Team information
    doc.add_paragraph()
    team_info = doc.add_paragraph()
    team_info.add_run('Team: ').bold = True
    team_info.add_run(data.get('teamName', 'Not specified'))
    team_info.add_run('\nPitch Number: ').bold = True
    team_info.add_run(str(data.get('pitchNumber', 'Not specified')))
    team_info.add_run('\nSession: ').bold = True
    team_info.add_run(str(data.get('session', 'Not specified')))
    team_info.add_run('\nDate: ').bold = True
    team_info.add_run(datetime.now().strftime('%B %d, %Y'))
    
    # Executive Summary
    doc.add_heading('Executive Summary', 1)
    doc.add_paragraph(summary)
    
    # Detailed Scoring
    doc.add_heading('Detailed Evaluation', 1)
    
    for section in data.get('scoringSections', []):
        # Section heading
        section_heading = doc.add_heading(section['title'], 2)
        
        # Score and weight information
        score_info = doc.add_paragraph()
        score_info.add_run('Score: ').bold = True
        score_info.add_run(f"{section['score']:.1f}/10")
        score_info.add_run('\nWeight: ').bold = True
        score_info.add_run(f"{section['weight']}%")
        
        # Question scores
        if section.get('questionScores'):
            scores_table = doc.add_table(rows=1, cols=2)
            scores_table.style = 'Table Grid'
            header_cells = scores_table.rows[0].cells
            header_cells[0].text = 'Question'
            header_cells[1].text = 'Score'
            
            for question, score in section['questionScores'].items():
                row_cells = scores_table.add_row().cells
                row_cells[0].text = f"Question {int(question) + 1}"
                row_cells[1].text = f"{score}/10"
        
        # Section feedback
        if section.get('feedback'):
            doc.add_paragraph()
            feedback_para = doc.add_paragraph()
            feedback_para.add_run('Feedback: ').bold = True
            feedback_para.add_run(section['feedback'])
        
        doc.add_paragraph()  # Add spacing between sections
    
    # General Feedback
    if data.get('generalFeedback'):
        doc.add_heading('General Feedback', 1)
        doc.add_paragraph(data['generalFeedback'])
    
    # Format the document
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(11)
            run.font.name = 'Calibri'
    
    # Save to memory stream
    doc_stream = io.BytesIO()
    doc.save(doc_stream)
    doc_stream.seek(0)
    
    return doc_stream

def retry_on_quota_exceeded():
    """Decorator to handle quota exceeded errors with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            max_retries = 5
            base_delay = 1
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "quota exceeded" in str(e).lower() and attempt < max_retries - 1:
                        delay = (base_delay * 2 ** attempt) + (random.uniform(0, 1))
                        logging.warning(f"Quota exceeded. Retrying in {delay:.2f} seconds. Attempt {attempt + 1}/{max_retries}")
                        time.sleep(delay)
                    else:
                        raise
            
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

@retry_on_quota_exceeded()
def generate_summary(feedback_data):
    """
    Generate a comprehensive summary using Groq's chat API.
    """
    # Prepare structured prompt
    sections_text = []
    for section in feedback_data.get('scoringSections', []):
        sections_text.append(f"\n{section['title']} (Score: {section['score']:.1f}/10):\n{section.get('feedback', 'No feedback provided')}")
    
    prompt = f"""
    Please provide a professional and constructive executive summary of the following pitch feedback:
    
    Team: {feedback_data.get('teamName')}
    Pitch Number: {feedback_data.get('pitchNumber')}
    Session: {feedback_data.get('session')}
    
    Detailed Feedback:
    {"".join(sections_text)}
    
    General Feedback:
    {feedback_data.get('generalFeedback', 'No general feedback provided')}
    
    Please structure the summary to include:
    1. Overall assessment
    2. Key strengths
    3. Areas for improvement
    4. Strategic recommendations
    
    Keep the tone constructive and professional.
    """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192"  
        )
        
        summary = chat_completion.choices[0].message.content
        
        if not summary:
            raise ValueError("Empty response received from Groq")
        
        return summary
    
    except Exception as e:
        logging.error(f"Error during summarization: {str(e)}", exc_info=True)
        raise

def generate_judge_feedback(data):
    """
    Compile judge feedback from available information.
    
    Args:
        data (dict): Feedback data
    
    Returns:
        str: Formatted judge feedback
    """
    feedback_parts = []
    
    # Use section feedbacks as judge perspectives
    for section in data.get('scoringSections', []):
        if section.get('feedback'):
            feedback_parts.append(f"Judge: {section.get('title', 'Evaluation')} - {section['feedback']}")
    
    # Add general feedback if available
    if data.get('generalFeedback'):
        feedback_parts.append(f"Overall Feedback: {data['generalFeedback']}")
    
    return '\n\n'.join(feedback_parts) or 'No detailed judge feedback available'

def generate_comprehensive_summary(data):
    """
    Generate a comprehensive summary of the startup pitch.
    
    Args:
        data (dict): Feedback data for the startup
    
    Returns:
        dict: Comprehensive summary with key metrics
    """
    summary = {
        'Overall Score': calculate_overall_score(data),
        'AI Analysis': generate_ai_analysis(data),
        'Judge Feedback Summaries': generate_judge_feedback(data)
    }
    return summary


def calculate_overall_score(data):
    """
    Calculate the overall score based on different scoring sections.
    
    Args:
        data (dict): Feedback data
    
    Returns:
        float: Calculated overall score
    """
    # If scoring sections exist, calculate weighted average
    if data.get('sectionScores'):
        total_weighted_score = sum(
            section['rawAverage'] * section.get('maxPoints', 1) 
            for section in data['sectionScores'].values()
        )
        total_weight = sum(
            section.get('maxPoints', 1) 
            for section in data['sectionScores'].values()
        )
        return total_weighted_score / total_weight if total_weight > 0 else 0
    
    # Fallback to total score if available
    return data.get('totalScore', 0)


def generate_ai_analysis(data):
    """
    Generate AI-driven analysis of the startup pitch.
    
    Args:
        data (dict): Feedback data
    
    Returns:
        str: Formatted AI analysis
    """
    strengths = []
    improvements = []
    recommendations = []

    # Extract strengths from scoring sections
    for section in data.get('scoringSections', []):
        if section.get('score', 0) > 8:
            strengths.append(f"Strong {section.get('title', 'area')}")
        elif section.get('score', 0) < 7:
            improvements.append(f"Improve {section.get('title', 'area')}")

    # Add general feedback insights
    if data.get('generalFeedback'):
        recommendations.append(data['generalFeedback'])

    return f"STRENGTHS:\n{', '.join(strengths) or '1. No specific strengths identified'}\n\nAREAS FOR IMPROVEMENT:\n{', '.join(improvements) or '1. No significant improvement areas identified'}\n\nRECOMMENDATIONS:\n{', '.join(recommendations) or '1. Continue refining pitch strategy'}"


@app.route("/summarize_feedback", methods=["POST"])
def summarize_feedback():
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Generate summary
        ai_summary = generate_summary(data)
        
        # Calculate overall score
        overall_score = calculate_overall_score(data)
        
        # Extract scoring sections
        scoring_sections = data.get('scoringSections', [])
        
        # Prepare CSV data
        output = io.StringIO()
        writer = csv.writer(output, lineterminator='\n')
        
        # Write metadata section
        writer.writerow(['Pitch Evaluation Summary'])
        writer.writerow([''])  # Empty row for spacing
        writer.writerow(['Basic Information'])
        writer.writerow(['Team Name', data.get('teamName', 'Not specified')])
        writer.writerow(['Pitch Number', data.get('pitchNumber', 'N/A')])
        writer.writerow(['Session', data.get('session', 'N/A')])
        writer.writerow(['Overall Score', f"{overall_score:.2f}/10"])
        writer.writerow([''])  # Empty row for spacing

        # Write scoring sections
        writer.writerow(['Detailed Scores'])
        writer.writerow(['Category', 'Score', 'Feedback'])
        for section in scoring_sections:
            writer.writerow([
                section.get('title', 'N/A'),
                f"{section.get('score', 0):.1f}/10",
                section.get('feedback', 'No feedback provided')
            ])
        writer.writerow([''])  # Empty row for spacing

        # Write general feedback
        writer.writerow(['General Feedback'])
        writer.writerow([data.get('generalFeedback', 'No general feedback provided')])
        writer.writerow([''])  # Empty row for spacing

        # Write AI Summary
        writer.writerow(['AI Analysis'])
        for paragraph in ai_summary.split('\n'):
            if paragraph.strip():  # Only write non-empty paragraphs
                writer.writerow([paragraph.strip()])

        # Create CSV file in memory
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='feedback_summary.csv'
        )
    except Exception as e:
        logging.error(f"Error processing feedback: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while processing the feedback"}), 500


@app.route("/download_feedback_csv/<pitch_id>", methods=["GET"])
def download_feedback_csv(pitch_id):
    # Simulate fetching data for the given pitch ID
    data = {
        "pitch_id": pitch_id,
        "feedback": "This is a sample feedback for the pitch.",
        "score": 85,
        "comments": "Strong potential with innovative solution."
    }
    
    # Return the data in raw buffer form
    return jsonify(data), 200


# Helper function to get pitch data (implement according to your data storage)
def get_pitch_data(pitch_id):
    """
    Retrieve pitch data from your storage system
    Args:
        pitch_id (str): The ID of the pitch
    Returns:
        dict: The pitch data
    """
    # Implement this according to your data storage solution
    # Example:
    # return db.pitches.find_one({"pitch_id": pitch_id})
    pass

# New route for handling dynamic question configuration
@app.route('/api/configure-questions', methods=['POST'])
def configure_questions():
    try:
        data = request.json
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid data format"}), 400

        # Validate the configuration structure
        if 'categories' not in data:
            return jsonify({"error": "Missing 'categories' in configuration"}), 400

        for category in data['categories']:
            if not all(key in category for key in ['name', 'weight', 'questions']):
                return jsonify({"error": "Invalid category structure"}), 400
            
            if not isinstance(category['questions'], list):
                return jsonify({"error": f"Questions for category {category['name']} must be a list"}), 400
                
            for question in category['questions']:
                if not all(key in question for key in ['id', 'text', 'weight']):
                    return jsonify({"error": f"Invalid question structure in category {category['name']}"}), 400

        # Store the configuration
        app.config['QUESTIONS_CONFIG'] = data
        
        # Update the ranking processor with new configuration
        init_ranking_processor(api_key=os.getenv('GROQ_API_KEY'))

        return jsonify({
            "message": "Questions configuration updated successfully",
            "config": data
        }), 200
    except Exception as e:
        logging.error(f"Error configuring questions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/results/export', methods=['GET'])
def export_results():
    # Return a hardcoded response simulating the results export
    response_data = [
        {
            "scoringTime": "2024-12-12T17:44:09+03:00",  # Current local time
            "totalScore": 85,
            "meetStartup": True,
            "mentorStartup": False,
            "nominateNextRound": True,
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
                    "isSkipped": False,
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
                    "isSkipped": False
                }
            }
        }
    ]

    return jsonify(response_data), 200

def fetch_results_from_database():
    # Implement your database logic here
    return []  # Placeholder for actual data fetching

@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Process the feedback data
    scoring_time = data.get('scoringTime')
    total_score = data.get('totalScore')
    meet_startup = data.get('meetStartup')
    mentor_startup = data.get('mentorStartup')
    nominate_next_round = data.get('nominateNextRound')
    overall_feedback = data.get('overallFeedback')
    judge_id = data.get('judgeId')
    startup_id = data.get('startupId')
    round_id = data.get('roundId')
    section_scores = data.get('sectionScores', {})
    raw_form_data = data.get('rawFormData', {})
    
    # Generate summary and overall score
    overall_score = calculate_overall_score({'sectionScores': section_scores})
    summary = generate_summary(data)  # Ensure summary is defined here
    
    # Create response data
    response_data = {
        'status': 'success',
        'overallScore': overall_score,
        'summary': summary,
        'feedback': overall_feedback
    }
    
    return jsonify(response_data), 200

def create_csv_report(startup_id, round_id, judge_id, overall_feedback, section_scores, total_score, summary):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(['Pitch Evaluation Summary'])
    writer.writerow([''])  # Empty row for spacing
    writer.writerow(['Basic Information'])
    writer.writerow(['Startup ID', startup_id])
    writer.writerow(['Round ID', round_id])
    writer.writerow(['Judge ID', judge_id])
    writer.writerow(['Overall Score', f"{total_score:.2f}/10"])
    writer.writerow([''])  # Empty row for spacing

    # Write scoring sections
    writer.writerow(['Detailed Scores'])
    writer.writerow(['Category', 'Score', 'Feedback'])
    for section in section_scores.values():
        writer.writerow([
            section.get('title', 'N/A'),
            f"{section.get('rawAverage', 0):.1f}/10",
            section.get('feedback', 'No feedback provided')
        ])
    writer.writerow([''])  # Empty row for spacing

    # Write general feedback
    writer.writerow(['General Feedback'])
    writer.writerow([overall_feedback])
    writer.writerow([''])  # Empty row for spacing

    # Write AI Summary
    writer.writerow(['AI Analysis'])
    for paragraph in summary.split('\n'):
        if paragraph.strip():  # Only write non-empty paragraphs
            writer.writerow([paragraph.strip()])

    # Create CSV file in memory
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8'))

if __name__ == "__main__":
    try:
        # Get port from environment variable for deployment platforms
        port = int(os.environ.get("PORT", 5000))
        
        # Try different ports if default port is in use (local development)
        ports = [port] + [p for p in [5000, 5001, 5002, 8080, 8081] if p != port]
        
        for try_port in ports:
            try:
                logging.info(f"Attempting to start server on port {try_port}")
                app.run(
                    host="0.0.0.0",  # Allow external connections
                    port=try_port,
                    debug=os.environ.get("FLASK_ENV") == "development"
                )
                break
            except OSError as e:
                if try_port == ports[-1]:
                    logging.error(f"Could not bind to any ports in {ports}. Error: {str(e)}")
                    raise
                else:
                    logging.warning(f"Port {try_port} is in use, trying next port")
                    continue
    except Exception as e:
        logging.error(f"Failed to start server: {str(e)}")
        raise