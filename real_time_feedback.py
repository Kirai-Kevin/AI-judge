from flask import Blueprint, request, jsonify
import logging
from groq import Groq
import os

# Initialize the blueprint
real_time_feedback_bp = Blueprint('real_time_feedback', __name__)

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Logging
logging.basicConfig(level=logging.INFO)

def clean_ai_response(response: str) -> str:
    """
    Clean up the AI response to remove asterisks and ensure the output is presentable.
    """
    return response.replace('*', '').strip()

# Function to generate AI analysis of the feedback
def generate_feedback_analysis(feedback):
    """
    Generate an AI-generated feedback analysis using Groq.
    """
    prompt = f"""
    Based on the following feedback, provide a quick analysis of the startup's strengths and weaknesses:

    Feedback:
    {feedback}

    Provide a concise summary highlighting key strengths and areas for improvement.
    """

    try:
        # Make request to Groq API
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        raw_analysis = response.choices[0].message.content
        return clean_ai_response(raw_analysis)
    except Exception as e:
        logging.error(f"Error generating feedback analysis: {e}")
        return "Error generating feedback analysis. Please try again later."

# Route to handle real-time feedback submission
@real_time_feedback_bp.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    """
    API endpoint to handle judge feedback submission and provide real-time AI-generated analysis.
    """
    try:
        # Get the feedback data from the request
        data = request.json
        feedback = data.get("feedback")

        if not feedback:
            return jsonify({"error": "No feedback provided."}), 400

        # Generate real-time analysis using Groq
        feedback_analysis = generate_feedback_analysis(feedback)

        return jsonify({
            "feedback_analysis": feedback_analysis,
        }), 200

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500
