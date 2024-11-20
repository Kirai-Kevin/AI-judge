from flask import Blueprint, request, send_file
import pandas as pd
from io import StringIO
import csv
from datetime import datetime
from typing import List, Dict
import numpy as np
from groq import Groq
import os
from tempfile import NamedTemporaryFile
import re

rankings_bp = Blueprint('rankings', __name__)

class StartupRankingProcessor:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.category_weights = {
            'problem': 0.15,
            'solution': 0.15,
            'innovation': 0.12,
            'team': 0.12,
            'business_model': 0.12,
            'market_opportunity': 0.12,
            'technical_feasibility': 0.10,
            'execution_strategy': 0.07,
            'communication': 0.05
        }

    def clean_analysis_text(self, text: str) -> str:
        """Clean the AI analysis output to remove markdown and special characters"""
        # Remove markdown asterisks
        text = re.sub(r'\*+', '', text)
        
        # Remove extra newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Clean up any remaining markdown syntax
        text = re.sub(r'#{1,6}\s', '', text)
        
        # Remove any remaining special characters
        text = text.replace('`', '')
        
        return text.strip()

    def calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted score based on category weights"""
        total_score = 0
        for category, score in scores.items():
            if category in self.category_weights:
                total_score += score * self.category_weights[category]
        return round(total_score, 2)

    def analyze_feedback(self, feedback: str) -> str:
        """Generate AI analysis of the feedback"""
        prompt = f"""
        Analyze the following startup feedback and provide a clear, structured analysis:

        {feedback}
        
        Format your response in this style:
        STRENGTHS:
        1. [First key strength]
        2. [Second key strength]

        AREAS FOR IMPROVEMENT:
        1. [First improvement area]
        2. [Second improvement area]

        RECOMMENDATIONS:
        1. [First specific recommendation]
        2. [Second specific recommendation]
        
        Keep the response professional and actionable. Do not use any markdown formatting or special characters.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            analysis = response.choices[0].message.content.strip()
            return self.clean_analysis_text(analysis)
        except Exception as e:
            return f"Error generating analysis: {str(e)}"

    def process_rankings(self, startup_feedback_list: List[Dict]) -> pd.DataFrame:
        """Process all startup feedback and create rankings"""
        rankings_data = []
        
        for startup_data in startup_feedback_list:
            startup_name = startup_data.get('startup_name', 'Unknown')
            judges_feedback = startup_data.get('judges_feedback', [])
            
            # Average scores across judges
            aggregated_scores = {}
            for category in self.category_weights.keys():
                scores = [judge.get('scores', {}).get(category, 0) for judge in judges_feedback]
                aggregated_scores[category] = np.mean(scores) if scores else 0
            
            # Calculate weighted score
            weighted_score = self.calculate_weighted_score(aggregated_scores)
            
            # Combine all feedback for AI analysis
            combined_feedback = "\n".join([judge.get('feedback', '') for judge in judges_feedback])
            ai_analysis = self.analyze_feedback(combined_feedback)
            
            rankings_data.append({
                'Startup Name': startup_name,
                'Overall Score': weighted_score,
                'Rank': None,  # Will be filled later
                'AI Analysis': ai_analysis,
                **aggregated_scores  # Include individual category scores
            })
        
        # Create DataFrame and sort by overall score
        df = pd.DataFrame(rankings_data)
        df = df.sort_values('Overall Score', ascending=False)
        df['Rank'] = range(1, len(df) + 1)
        
        return df

@rankings_bp.route('/download_rankings', methods=['POST'])
def download_rankings():
    """Generate and download CSV file with startup rankings"""
    try:
        # Get startup feedback data from request
        data = request.json
        startup_feedback_list = data.get('startup_feedback', [])
        
        if not startup_feedback_list:
            return {'error': 'No feedback data provided'}, 400
        
        # Process rankings
        processor = StartupRankingProcessor(api_key=os.getenv('GROQ_API_KEY'))
        rankings_df = processor.process_rankings(startup_feedback_list)
        
        # Create temporary file
        temp_file = NamedTemporaryFile(delete=False, suffix='.csv')
        
        # Save to CSV
        rankings_df.to_csv(temp_file.name, index=False)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'startup_rankings_{timestamp}.csv'
        
        return send_file(
            temp_file.name,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return {'error': str(e)}, 500