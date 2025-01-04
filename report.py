import os
import textwrap
from flask import Blueprint, request, jsonify
import openai
import logging

report_bp = Blueprint('report', __name__)

__all__ = ['report_bp', 'generate_feedback_summary']
# Check if the API key is set


def generate_feedback_summary(feedback: dict):
    from app import clean_ai_response
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
        chat_completion = openai.chat.completions.create(
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
        logging.error(f"Error generating feedback summary: {str(e)}")
        return f"Error generating feedback summary: {str(e)}"
