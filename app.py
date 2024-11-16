import os
import logging
from flask import Flask, request, jsonify
import random
from groq import Groq
from functools import wraps
from dotenv import load_dotenv
import time
from report import report_bp, generate_feedback_summary
from real_time_feedback import real_time_feedback_bp
from feedback_processor import feedback_processor_bp


load_dotenv()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(report_bp, url_prefix='/report')
app.register_blueprint(real_time_feedback_bp, url_prefix="/real_time_feedback")
app.register_blueprint(feedback_processor_bp, url_prefix='/feedback_processor')


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

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
                        logger.warning(f"Quota exceeded. Retrying in {delay:.2f} seconds. Attempt {attempt + 1}/{max_retries}")
                        time.sleep(delay)
                    else:
                        raise
            
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

@retry_on_quota_exceeded()
def generate_summary(feedback_list):
    """
    Summarize feedback using Groq's chat API with retry handling.
    """
    prompt = f"""
    Summarize the following feedback into three concise, actionable insights:
    Feedback:
    {feedback_list}
    Provide clear and constructive points.
    """
    
    try:
        # Call the Groq API chat completion method
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
        logger.error(f"Error during summarization: {str(e)}", exc_info=True)
        raise

@app.route("/summarize_feedback", methods=["POST"])
def summarize_feedback():
    """
    API endpoint to summarize feedback using Groq with retry handling.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.json
        feedback_list = data.get("feedback")
        
        if not feedback_list:
            return jsonify({"error": "No feedback provided"}), 400
        
        if not isinstance(feedback_list, (str, list)):
            return jsonify({"error": "Feedback must be a string or list"}), 400

        if isinstance(feedback_list, list):
            feedback_list = "\n".join(str(item) for item in feedback_list)

        try:
            summary = generate_feedback_summary({"high_level": feedback_list, "problem": "", "solution": "", "innovation": "", "team": "", "business_model": "", "market_opportunity": "", "technical_feasibility": "", "execution_strategy": "", "communication": ""})
            
            return jsonify({
                "summary": summary,
                "status": "success"
            }), 200

        except Exception as e:
            return jsonify({
                "error": "An error occurred while processing the feedback",
                "details": str(e)
            }), 500

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e) if app.debug else None
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
