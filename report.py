import os
import textwrap
from flask import Blueprint
from groq import Groq
from dotenv import load_dotenv

# Create a blueprint
report_bp = Blueprint('report', __name__)
load_dotenv()



# Groq API setup
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Function to clean up the AI response
def clean_ai_response(response: str) -> str:
    """
    Clean up the AI response to remove asterisks and ensure the output is presentable.
    """
    return response.replace('*', '').strip()

# Summarization function using Groq API with Gemini-Pro
def generate_feedback_summary(feedback: dict):
    """
    Summarize the judges' feedback for each startup using llama-8b-8192 model.
    """

    # Prepare the feedback prompt for Gemini-Pro
    prompt = textwrap.dedent(f"""
        Please generate a detailed and high-level summary for the following feedback for the startup:

        **High-level Summary of Feedback:**
        {feedback['high_level']}

        **Detailed Feedback per Scoring Category:**
        Problem: {feedback['problem']}
        Solution: {feedback['solution']}
        Innovation: {feedback['innovation']}
        Team: {feedback['team']}
        Business Model: {feedback['business_model']}
        Market Opportunity: {feedback['market_opportunity']}
        Technical Feasibility: {feedback['technical_feasibility']}
        Execution Strategy: {feedback['execution_strategy']}
        Communication: {feedback['communication']}

        Please provide actionable insights for both the judges and the startup.
    """)

    try:
        # Request a summary from Gemini-Pro using the Groq API
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model="llama3-8b-8192"
        )
        # Extract and clean the result
        raw_summary = chat_completion.choices[0].message.content
        cleaned_summary = clean_ai_response(raw_summary)
        return cleaned_summary

    except Exception as e:
        return f"Error generating feedback summary: {str(e)}"

# Flask route to generate feedback summary
@report_bp.route('/generate_summary', methods=['POST'])
def generate_summary():
    """
    API endpoint to generate a summary of feedback for a startup.
    """
    try:
        # Parse incoming JSON request
        from flask import request, jsonify
        data = request.json
        feedback = data.get("feedback")

        if not feedback:
            return jsonify({"error": "Feedback data is required."}), 400

        # Generate the summary
        summary = generate_feedback_summary(feedback)
        
        return jsonify({"summary": summary}), 200

    except Exception as e:
        from flask import jsonify
        return jsonify({"error": str(e)}), 500

