from flask import Blueprint, request, jsonify, send_file
import pandas as pd
import numpy as np
from groq import Groq
import os
from datetime import datetime
from tempfile import NamedTemporaryFile
import re
from typing import List, Dict
import logging
import zipfile

# Initialize logger
logger = logging.getLogger(__name__)

# Create the blueprint
rankings_bp = Blueprint('rankings', __name__)

# Create a global ranking processor instance
ranking_processor = None

def init_ranking_processor(api_key):
    global ranking_processor
    if ranking_processor is None:
        ranking_processor = StartupRankingProcessor(api_key=api_key)

@rankings_bp.route('/download', methods=['POST'])
def download_rankings():
    """Generate and download CSV files with startup rankings"""
    try:
        if ranking_processor is None:
            return jsonify({"error": "Ranking processor not initialized"}), 500

        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Process the rankings
        startup_list = [data] if isinstance(data, dict) else data
        if not startup_list:
            return jsonify({"error": "No startup data provided"}), 400

        # Create a temporary directory for our files
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        # Generate timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate both comprehensive and summary rankings
        try:
            comprehensive_rankings = ranking_processor.process_rankings(startup_list, comprehensive=True)
            summary_rankings = ranking_processor.process_rankings(startup_list, comprehensive=False)
            
            # Save to CSV files
            comprehensive_path = os.path.join(temp_dir, f'comprehensive_rankings_{timestamp}.csv')
            summary_path = os.path.join(temp_dir, f'summary_rankings_{timestamp}.csv')
            
            comprehensive_rankings.to_csv(comprehensive_path, index=False, encoding='utf-8-sig')
            summary_rankings.to_csv(summary_path, index=False, encoding='utf-8-sig')
            
            # Create a ZIP file containing both CSVs
            zip_filename = f'startup_rankings_{timestamp}.zip'
            zip_path = os.path.join(temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(comprehensive_path, os.path.basename(comprehensive_path))
                zipf.write(summary_path, os.path.basename(summary_path))
            
            # Clean up individual CSV files
            os.remove(comprehensive_path)
            os.remove(summary_path)
            
            # Send the ZIP file
            return send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name=zip_filename
            )
            
        except Exception as e:
            logger.error(f"Error processing rankings: {str(e)}")
            return jsonify({"error": f"Error processing rankings: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error generating rankings files: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary files in case of success or failure
        try:
            if 'zip_path' in locals():
                os.remove(zip_path)
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temporary files: {str(cleanup_error)}")

@rankings_bp.route('/generate', methods=['POST'])
def generate_rankings():
    """Generate rankings from startup evaluations"""
    try:
        if ranking_processor is None:
            return jsonify({"error": "Ranking processor not initialized"}), 500

        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Process the rankings
        startup_list = [data] if isinstance(data, dict) else data
        if not startup_list:
            return jsonify({"error": "No startup data provided"}), 400

        # Validate required fields
        for startup in startup_list:
            if 'startupId' not in startup:
                return jsonify({"error": "Missing required field: startupId"}), 400

        # Generate both comprehensive and summary rankings
        try:
            rankings = ranking_processor.process_rankings(startup_list, comprehensive=True)
            return jsonify({
                "message": "Rankings generated successfully",
                "rankings": rankings.to_dict(orient='records') if not rankings.empty else []
            })
        except Exception as e:
            logger.error(f"Error processing rankings: {str(e)}")
            return jsonify({"error": f"Error processing rankings: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Error generating rankings: {str(e)}")
        return jsonify({"error": str(e)}), 500

class StartupRankingProcessor:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        # Default weights if no configuration is provided
        self.category_weights = {}
        self.questions_config = {}
        
    def configure_questions(self, config: Dict):
        """Configure the questions and weights dynamically"""
        self.questions_config = config
        self.category_weights = {
            category['name'].lower().replace(' ', '_'): category['weight']
            for category in config.get('categories', [])
        }

    def _get_question_by_id(self, question_id: str) -> tuple:
        """Get question details by ID"""
        for category in self.questions_config.get('categories', []):
            for question in category.get('questions', []):
                if question['id'] == question_id:
                    return category['name'], question
        return None, None

    def calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted score based on dynamic category weights"""
        if not self.category_weights:
            return 0.0
            
        total_score = 0
        for category, score in scores.items():
            weight = self.category_weights.get(category.lower().replace(' ', '_'), 0)
            total_score += score * weight
        return round(total_score, 2)

    def clean_analysis_text(self, text: str) -> str:
        """Clean the AI analysis output to remove markdown and special characters"""
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'#{1,6}\s', '', text)
        text = text.replace('`', '')
        return text.strip()

    def process_rankings(self, startup_feedback_list: List[Dict], comprehensive: bool = False) -> pd.DataFrame:
        """Process startup feedback and create rankings"""
        if comprehensive:
            return self._process_comprehensive_rankings(startup_feedback_list)
        else:
            return self._process_summary_rankings(startup_feedback_list)

    def _process_summary_rankings(self, startup_feedback_list: List[Dict]) -> pd.DataFrame:
        """Process summary rankings from startup feedback"""
        rankings_data = []
        
        for startup_data in startup_feedback_list:
            startup_id = startup_data.get('startupId')
            if not startup_id:
                continue

            # Get only the required startup info
            data = {
                'Startup ID': startup_id,
                'Overall Score': startup_data.get('averageScore', 0)
            }
            
            rankings_data.append(data)
        
        if not rankings_data:
            return pd.DataFrame()
            
        # Create DataFrame and sort by score
        df = pd.DataFrame(rankings_data)
        df = df.sort_values('Overall Score', ascending=False)
        df['Rank'] = range(1, len(df) + 1)
        
        return df

    def _process_comprehensive_rankings(self, startup_feedback_list: List[Dict]) -> pd.DataFrame:
        """Process comprehensive rankings with detailed criteria"""
        all_data = []
        
        for startup_data in startup_feedback_list:
            startup_id = startup_data.get('startupId')
            if not startup_id:
                continue
                
            base_data = {
                'Startup ID': startup_id,
                'Judge ID': startup_data.get('judgeId', 'Unknown'),
                'Overall Score': startup_data.get('averageScore', 0),
                'Overall Feedback': startup_data.get('feedback', '')
            }
            
            # Process each round
            for round_data in startup_data.get('individualScores', []):
                round_id = round_data.get('roundId', 'Unknown')
                round_base = {
                    **base_data,
                    'Round ID': round_id,
                    'Round Average': round_data.get('average', 0),
                    'Round Feedback': round_data.get('feedback', '')
                }
                
                # Process each criterion
                for criterion in round_data.get('criteria', []):
                    criterion_data = {
                        **round_base,
                        'Question': criterion.get('question', ''),
                        'Score': criterion.get('score', 0),
                        'Skipped': criterion.get('skipped', False)
                    }
                    all_data.append(criterion_data)
        
        if not all_data:
            return pd.DataFrame()
            
        # Create DataFrame and sort
        df = pd.DataFrame(all_data)
        df = df.sort_values(['Overall Score', 'Round Average', 'Score'], ascending=[False, False, False])
        
        return df

    def analyze_feedback(self, feedback: str) -> str:
        """Generate AI analysis of the feedback"""
        try:
            prompt = f"Analyze the following startup evaluation feedback and provide a concise summary:\n\n{feedback}"
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=300,
                top_p=1,
                stream=False
            )
            return self.clean_analysis_text(completion.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error generating AI analysis: {str(e)}")
            return "Error generating analysis"

    def summarize_judge_feedback(self, judge_feedback: Dict) -> str:
        """Generate a summary for individual judge feedback"""
        # [Previous implementation remains the same]
        feedback_text = judge_feedback.get('feedback', '').strip()
        
        if not feedback_text:
            return "No specific feedback provided."
        
        prompt = f"""
        Distill the key insights from this judge's feedback into a concise 2-3 sentence summary:

        {feedback_text}

        Focus on:
        - Most significant strengths
        - Critical areas for improvement
        - Any standout observations

        Respond with only the summary, avoiding any introductory phrases.
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            summary = response.choices[0].message.content.strip()
            
            # Final cleaning to remove any remaining introductory text
            summary = re.sub(r'^(here|the|this|in)\s+(is\s+)?(a\s+)?(summary|key\s+points?):?\s*', '', summary, flags=re.IGNORECASE).strip()
            
            # Ensure we have a meaningful summary
            if not summary:
                return "Concise observations were not generated."
            
            return self.clean_analysis_text(summary)
        except Exception as e:
            return f"Error generating summary: {str(e)}"