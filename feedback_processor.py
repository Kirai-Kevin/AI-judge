import pandas as pd
import json
from groq import Groq
from typing import List, Dict
from flask import Blueprint, request, jsonify
import os

# Create a blueprint
feedback_processor_bp = Blueprint('feedback_processor', __name__)

class FeedbackProcessor:
    def __init__(self, api_key: str):
        # Initialize the Groq client with the API key
        self.client = Groq(api_key=api_key)

    def process_startup_feedback(self, startup_data: Dict, judge_feedback: List[Dict]) -> Dict:
        """
        Process feedback for a single startup using Groq (formerly Claude)
        """
        # Aggregate feedback and scores
        aggregated_feedback = self._aggregate_feedback(judge_feedback)
        
        # Prepare prompt for Groq
        prompt = self._create_analysis_prompt(startup_data, aggregated_feedback)
        
        # Get analysis from Groq
        response = self.client.chat.completions.create(
            model="llama3-8b-8192",  
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Structure the response
        analysis = self._structure_response(response.choices[0].message.content)
        
        return {
            "startup_name": startup_data["name"],
            "analysis": analysis,
            "aggregate_scores": aggregated_feedback["scores"],
            "detailed_feedback": aggregated_feedback["feedback"]
        }
    
    def _aggregate_feedback(self, judge_feedback: List[Dict]) -> Dict:
        """
        Aggregate feedback from judges (example logic)
        """
        scores = [feedback.get('score', 0) for feedback in judge_feedback]
        feedback_comments = [feedback.get('comment', '') for feedback in judge_feedback]
        
        return {
            "scores": scores,
            "feedback": feedback_comments
        }

    def _create_analysis_prompt(self, startup_data: Dict, aggregated_feedback: Dict) -> str:
        """
        Create a prompt for Groq to analyze the feedback
        """
        prompt = f"""
        Startup Name: {startup_data['name']}
        
        Normalized Scores:
        {json.dumps(aggregated_feedback['scores'], indent=2)}
        
        Judge Feedback:
        {json.dumps(aggregated_feedback['feedback'], indent=2)}
        
        Provide a comprehensive analysis of the startup's strengths and weaknesses, 
        including any key trends, insights, and recommendations for improvement.
        """
        return prompt
    
    def _structure_response(self, response_content: str) -> str:
        """
        Structure the response content from Groq to fit the desired output format
        """
        
        return response_content.strip()



feedback_processor = FeedbackProcessor(api_key=os.environ.get('GROQ_API_KEY'))

@feedback_processor_bp.route('/process_feedback', methods=['POST'])
def process_startup_feedback():
    """
    Process feedback for a startup using the `FeedbackProcessor` instance
    """
    try:
        data = request.json
        startup_data = data.get("startup_data")
        judge_feedback = data.get("judge_feedback")

        if not startup_data or not judge_feedback:
            return jsonify({"error": "Startup data and judge feedback are required."}), 400

        # Use the FeedbackProcessor instance to process feedback
        result = feedback_processor.process_startup_feedback(startup_data, judge_feedback)
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@feedback_processor_bp.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """
    API endpoint to handle user input for startup data and judge feedback.
    """
    try:
        data = request.json
        startup_data = data.get("startup_data")
        judge_feedback = data.get("judge_feedback")

        if not startup_data or not judge_feedback:
            return jsonify({"error": "Startup data and judge feedback are required."}), 400

        # Use the FeedbackProcessor instance to process feedback
        result = feedback_processor.process_startup_feedback(startup_data, judge_feedback)
        
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
