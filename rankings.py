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

        # Validate required fields
        required_fields = ['startupId', 'evaluations']
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Missing required fields: {', '.join(required_fields)}"}), 400

        # Process the evaluation
        startup_list = [data]  # Wrap single startup data in a list
        rankings_df = ranking_processor.process_rankings(startup_list, comprehensive=True)
        
        # Convert DataFrame to JSON
        rankings_json = rankings_df.to_dict(orient='records')
        
        return jsonify({
            "message": "Rankings generated successfully",
            "rankings": rankings_json
        }), 200
        
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
        rankings_data = []
        
        for startup_data in startup_feedback_list:
            startup_id = startup_data.get('startup_id')
            if not startup_id:
                continue  # Skip entries without startup_id
                
            startup_name = startup_data.get('startup_name', 'Unknown')
            judges_feedback = startup_data.get('judges_feedback', [])
            
            # Calculate nomination and interest counts from judges_feedback
            nomination_count = sum(1 for judge in judges_feedback if judge.get('nominated_for_next_round', False))
            mentor_interest_count = sum(1 for judge in judges_feedback if judge.get('mentor_interest', False))
            hero_meetings_count = sum(1 for judge in judges_feedback if judge.get('hero_want_to_meet', False))
            
            judge_summaries = []
            subcategory_avg_scores = {}
            
            # Prepare aggregated scores dictionary
            aggregated_scores = {category: 0 for category in self.category_weights.keys()}
            
            for judge in judges_feedback:
                judge_id = judge.get('judge_id')
                if not judge_id:
                    continue  # Skip entries without judge_id
                    
                summary = self.summarize_judge_feedback(judge)
                judge_summaries.append(f"Judge {judge_id}: {summary}")
                
                # Aggregate category scores
                for category in aggregated_scores.keys():
                    score = judge.get('scores', {}).get(category, 0)
                    aggregated_scores[category] = score
            
            # Calculate weighted score
            weighted_score = self.calculate_weighted_score(aggregated_scores)
            
            # Combine all feedback for AI analysis
            combined_feedback = "\n".join([f"Judge {judge.get('judge_id', 'Unknown')}: {judge.get('feedback', '')}" 
                                        for judge in judges_feedback if judge.get('judge_id')])
            ai_analysis = self.analyze_feedback(combined_feedback) if combined_feedback else "No detailed feedback available."
            
            # Prepare subcategory average scores
            for category, subcategories in self.questions_config.get('categories', []):
                for subcat_idx, subcat in enumerate(subcategories.get('questions', [])):
                    subcategory_key = f"{category} - {subcat['text']}"
                    scores = [judge.get('detailed_scores', {}).get(category.lower().replace(' ', '_'), {}).get(subcat_idx, 0) 
                            for judge in judges_feedback if judge.get('judge_id')]
                    avg_score = round(np.mean(scores), 2) if scores else 0
                    subcategory_avg_scores[subcategory_key] = avg_score
            
            # Use the actual counts instead of converting to boolean
            ranking_entry = {
                'Startup ID': startup_id,
                'Startup Name': startup_name,
                'Overall Score': weighted_score,
                'Nominated for Next Round': nomination_count,  # Use actual count
                'Mentor Interest': mentor_interest_count,      # Use actual count
                'Heroes Want to Meet': hero_meetings_count,    # Use actual count
                'Rank': None,
                'AI Analysis': ai_analysis,
                'Judge Feedback Summaries': '\n\n'.join(judge_summaries),
                **aggregated_scores,
                **subcategory_avg_scores
            }
            
            rankings_data.append(ranking_entry)
        
        # Create DataFrame and sort
        df = pd.DataFrame(rankings_data)
        df = df.sort_values('Overall Score', ascending=False)
        df['Rank'] = range(1, len(df) + 1)
        
        return df

    def _process_comprehensive_rankings(self, startup_feedback_list: List[Dict]) -> pd.DataFrame:
        rankings_data = []
        
        for startup_data in startup_feedback_list:
            startup_id = startup_data.get('startupId')
            if not startup_id:
                continue
                
            startup_name = startup_data.get('startup_name', 'Unknown')
            evaluations = startup_data.get('evaluations', [])
            
            # Process each evaluation round
            for evaluation in evaluations:
                round_id = evaluation.get('roundId')
                responses = evaluation.get('responses', [])
                
                row_data = {
                    'Startup ID': startup_id,
                    'Startup Name': startup_name,
                    'Round ID': round_id,
                    'Overall Score': 0  # Initialize with default
                }
                
                # Process each question response
                category_scores = {}
                for response in responses:
                    question_id = response.get('questionId')
                    score = response.get('score', 0)
                    category_name, question = self._get_question_by_id(question_id)
                    
                    if category_name and question:
                        if category_name not in category_scores:
                            category_scores[category_name] = []
                        category_scores[category_name].append(score)
                        
                        # Add individual question score
                        col_name = f"{category_name} - {question['text']}"
                        row_data[col_name] = score
                
                # Calculate category averages and weighted score
                total_weighted_score = 0
                total_weight = 0
                
                for category in self.questions_config.get('categories', []):
                    category_name = category['name']
                    category_weight = category.get('weight', 0)
                    
                    if category_name in category_scores and category_scores[category_name]:
                        avg_score = np.mean(category_scores[category_name])
                        row_data[f'{category_name} Score'] = round(avg_score, 2)
                        total_weighted_score += avg_score * category_weight
                        total_weight += category_weight
                
                # Calculate overall score
                if total_weight > 0:
                    row_data['Overall Score'] = round(total_weighted_score / total_weight, 2)
                
                # Add nomination info
                nominations = startup_data.get('nominations', {})
                row_data['Nominated'] = nominations.get('isNominated', False)
                row_data['Mentored'] = nominations.get('willBeMentored', False)
                row_data['Meeting Requested'] = nominations.get('willBeMet', False)
                
                rankings_data.append(row_data)
        
        # Create DataFrame
        if not rankings_data:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['Startup ID', 'Startup Name', 'Round ID', 'Overall Score', 
                                      'Nominated', 'Mentored', 'Meeting Requested'])
        
        df = pd.DataFrame(rankings_data)
        
        # Sort by overall score and add rank
        df = df.sort_values('Overall Score', ascending=False)
        df['Rank'] = range(1, len(df) + 1)
        
        # Reorder columns
        first_columns = ['Rank', 'Startup ID', 'Startup Name', 'Round ID', 'Overall Score']
        other_columns = [col for col in df.columns if col not in first_columns]
        df = df[first_columns + sorted(other_columns)]
        
        return df

    def analyze_feedback(self, feedback: str) -> str:
        """Generate AI analysis of the feedback"""
        # [Previous implementation remains the same]
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