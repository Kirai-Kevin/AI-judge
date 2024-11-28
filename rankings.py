from flask import Blueprint, request, send_file
import pandas as pd
import numpy as np
from groq import Groq
import os
from datetime import datetime
from tempfile import NamedTemporaryFile
import re
from typing import List, Dict

rankings_bp = Blueprint('rankings', __name__)

class StartupRankingProcessor:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.category_weights = {
            'problem': 0.10,
            'solution': 0.10,
            'innovation': 0.10,
            'team': 0.20,
            'business_model': 0.10,
            'market_opportunity': 0.10,
            'technical_feasibility': 0.10,
            'execution_strategy': 0.10,
            'communication': 0.10
        }
        
        self.comprehensive_columns = {
            'Problem': [
                'Is there a clear problem?',
                'Is there evidence to support the importance of the problem?',
                'Is the problem solvable?',
                'How obsessed is the team on the problem?'
            ],
            'Solution': [
                'Does the solution make sense?',
                'Is there a clear vision of what the solution should be?',
                'Is the solution feasible to be developed by the team?'
            ],
            'Innovation': [
                'How novel is the proposed AI application?',
                'Does it solve a problem in a new or unique way?'
            ],
            'Team': [
                'Does the team have the necessary skills and expertise to execute their vision or to build a startup from scratch to success?',
                'Do they have strong leadership',
                'Is there good team dynamics and teamwork?',
                'Does the team show itself to have agility and adaptability to adjust to challenges they might face?'
            ],
            'Business Model': [
                'Does the revenue or business model make sense?',
                'Does the revenue or business model make sense?'
            ],
            'Market Opportunity': [
                'Is there a clear market need for the proposed AI application?',
                'How large is the potential market?',
                'How does the team plan to monetize the product?'
            ],
            'Technical Feasibility': [
                'Is the proposed AI application technically feasible?',
                'Does the team demonstrate a strong understanding of the AI technology and its capabilities?'
            ],
            'Execution Strategy': [
                'Does the team\'s strategy make sense at this stage?',
                'Do they have a clear idea on how to grow and scale the company?'
            ],
            'Communication': [
                'Does the team have a clear vision?',
                'Was the pitch clear, concise, and engaging?',
                'Did the team effectively communicate their ideas and address potential concerns?'
            ]
        }

    def clean_analysis_text(self, text: str) -> str:
        """Clean the AI analysis output to remove markdown and special characters"""
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'#{1,6}\s', '', text)
        text = text.replace('`', '')
        return text.strip()

    def calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted score based on category weights"""
        total_score = 0
        for category, score in scores.items():
            if category in self.category_weights:
                total_score += score * self.category_weights[category]
        return round(total_score, 2)

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
            for category, subcategories in self.comprehensive_columns.items():
                for subcat_idx, subcat in enumerate(subcategories):
                    subcategory_key = f"{category} - {subcat}"
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
            startup_id = startup_data.get('startup_id')
            if not startup_id:
                continue  # Skip entries without startup_id
                
            startup_name = startup_data.get('startup_name', 'Unknown')
            judges_feedback = startup_data.get('judges_feedback', [])
            
            # Track category-level scores across judges
            startup_category_scores = {category: [] for category in self.comprehensive_columns.keys()}
            
            # Count total nominations and interest for reference
            total_nominations = sum(1 for judge in judges_feedback if judge.get('nominated_for_next_round', False))
            total_mentor_interest = sum(1 for judge in judges_feedback if judge.get('mentor_interest', False))
            total_hero_meetings = sum(1 for judge in judges_feedback if judge.get('hero_want_to_meet', False))
            
            for judge in judges_feedback:
                judge_id = judge.get('judge_id')
                if not judge_id:
                    continue  # Skip entries without judge_id
                    
                row_data = {
                    'Startup ID': startup_id,
                    'Startup Name': startup_name,
                    'Judge ID': judge_id,
                    'Overall Judge Score': 0
                }
                
                # Set individual judge's nomination status as boolean
                row_data['Nominated for Next Round'] = bool(judge.get('nominated_for_next_round', False))
                row_data['Mentor Interest'] = bool(judge.get('mentor_interest', False))
                row_data['Heroes Want to Meet'] = bool(judge.get('hero_want_to_meet', False))
                
                # Calculate scores for each category and subcategory
                overall_judge_scores = []
                
                for category, subcategories in self.comprehensive_columns.items():
                    category_key = category.lower().replace(' ', '_')
                    judge_detailed_scores = judge.get('detailed_scores', {}).get(category_key, {})
                    
                    category_scores = []
                    
                    for subcat_idx, subcat in enumerate(subcategories):
                        col_name = f"{category} - {subcat}"
                        score = judge_detailed_scores.get(subcat_idx, 0)
                        row_data[col_name] = score
                        category_scores.append(score)
                        overall_judge_scores.append(score)
                    
                    if category_scores:
                        category_avg = round(np.mean(category_scores), 2)
                        row_data[f'{category} Overall Score'] = category_avg
                        startup_category_scores[category].append(category_avg)
                
                if overall_judge_scores:
                    row_data['Overall Judge Score'] = round(np.mean(overall_judge_scores), 2)
                
                row_data['Startup Overall Score'] = round(row_data['Overall Judge Score'] / 10, 2)
                
                rankings_data.append(row_data)
        
        # Create DataFrame
        df = pd.DataFrame(rankings_data)

        # Sort by startup's overall score and then by startup ID and judge ID
        df = df.sort_values(['Startup Overall Score', 'Startup ID', 'Judge ID'], 
                            ascending=[False, True, True])

        # Add overall startup rank
        startup_avg_scores = df.groupby(['Startup ID', 'Startup Name'])['Overall Judge Score'].mean().reset_index()
        startup_avg_scores = startup_avg_scores.sort_values('Overall Judge Score', ascending=False)
        startup_avg_scores['Startup Rank'] = range(1, len(startup_avg_scores) + 1)

        # Merge ranks back to the main dataframe
        df = df.merge(startup_avg_scores[['Startup ID', 'Startup Rank']], on='Startup ID', how='left')

        # Reorder columns
        columns_order = ['Startup Rank', 'Startup ID', 'Startup Name', 'Judge ID', 'Overall Judge Score', 
                        'Startup Overall Score', 'Nominated for Next Round', 
                        'Mentor Interest', 'Heroes Want to Meet']

        category_overall_scores = [col for col in df.columns if col.startswith('Startup ') and col.endswith('Overall Score')]
        columns_order.extend(sorted(category_overall_scores))
        
        detailed_columns = [col for col in df.columns if col not in columns_order]
        columns_order.extend(sorted(detailed_columns))

        df = df[columns_order]
        
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
        
        # Generate both ranking types
        summary_rankings = processor.process_rankings(startup_feedback_list, comprehensive=False)
        comprehensive_rankings = processor.process_rankings(startup_feedback_list, comprehensive=True)
        
        # Create temporary files
        summary_temp_file = NamedTemporaryFile(delete=False, suffix='.csv')
        comprehensive_temp_file = NamedTemporaryFile(delete=False, suffix='.csv')
        
        # Save to CSV with specific encoding for special characters
        summary_rankings.to_csv(summary_temp_file.name, index=False, encoding='utf-8-sig')
        comprehensive_rankings.to_csv(comprehensive_temp_file.name, index=False, encoding='utf-8-sig')
        
        # Generate filenames with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_filename = f'startup_rankings_{timestamp}.csv'
        comprehensive_filename = f'startup_comprehensive_rankings_{timestamp}.csv'
        
        # Return file paths or create a custom response
        return {
            'summary_file_path': summary_temp_file.name,
            'comprehensive_file_path': comprehensive_temp_file.name,
            'summary_filename': summary_filename,
            'comprehensive_filename': comprehensive_filename
        }
        
    except Exception as e:
        return {'error': str(e)}, 500