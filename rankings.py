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
        
        # Define detailed subcategories for comprehensive output
        self.comprehensive_columns = {
            'Problem': [
                'Is there a clear problem?',
                'Is there evidence to support the importance of the problem?',
                'Is the problem solvable?',
                'How obsessed is the team with solving the problem?'
            ],
            'Solution': [
                'Does the solution make sense?',
                'Is there a clear vision of what the solution should be?',
                'Is the solution innovative?',
                'Is the solution feasible?'
            ],
            'Innovation': [
                'Is the innovation significant?',
                'Does it create new opportunities?',
                'Is it differentiated from existing solutions?'
            ],
            'Team': [
                'Does the team have relevant experience?',
                'Is the team composition balanced?',
                'Do they show strong leadership potential?'
            ],
            'Business Model': [
                'Is the business model clear?',
                'Is it scalable?',
                'Are the revenue streams well-defined?'
            ],
            'Market Opportunity': [
                'Is the market size significant?',
                'Is the growth potential strong?',
                'Is the competitive advantage sustainable?'
            ],
            'Technical Feasibility': [
                'Is the technical approach sound?',
                'Are the technical challenges well understood?',
                'Does the team have the technical capability?'
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
        """Process rankings for summary output"""
        rankings_data = []
        
        for startup_data in startup_feedback_list:
            startup_name = startup_data.get('startup_name', 'Unknown')
            judges_feedback = startup_data.get('judges_feedback', [])
            
            # Process judge summaries
            judge_summaries = []
            for i, judge in enumerate(judges_feedback, 1):
                summary = self.summarize_judge_feedback(judge)
                judge_summaries.append(f"Judge {i}: {summary}")
            
            # Aggregate scores
            aggregated_scores = {}
            for category in self.category_weights.keys():
                scores = [judge.get('scores', {}).get(category, 0) for judge in judges_feedback]
                aggregated_scores[category] = round(np.mean(scores), 2) if scores else 0
            
            # Calculate weighted score
            weighted_score = self.calculate_weighted_score(aggregated_scores)
            
            # Combine all feedback for AI analysis
            combined_feedback = "\n".join([judge.get('feedback', '') for judge in judges_feedback])
            ai_analysis = self.analyze_feedback(combined_feedback)
            
            rankings_data.append({
                'Startup Name': startup_name,
                'Overall Score': weighted_score,
                'Rank': None,
                'AI Analysis': ai_analysis,
                'Judge Feedback Summaries': '\n\n'.join(judge_summaries),
                **aggregated_scores
            })
        
        # Create DataFrame and sort by overall score
        df = pd.DataFrame(rankings_data)
        df = df.sort_values('Overall Score', ascending=False)
        df['Rank'] = range(1, len(df) + 1)
        
        # Round numeric columns
        numeric_columns = ['Overall Score'] + list(self.category_weights.keys())
        df[numeric_columns] = df[numeric_columns].round(2)
        
        # Reorder columns
        columns = ['Rank', 'Startup Name', 'Overall Score']
        score_columns = list(self.category_weights.keys())
        summary_columns = ['AI Analysis', 'Judge Feedback Summaries']
        df = df[columns + score_columns + summary_columns]
        
        return df

    def _process_comprehensive_rankings(self, startup_feedback_list: List[Dict]) -> pd.DataFrame:
        """Process rankings for comprehensive output with detailed judge scores and category averages"""
        rankings_data = []

        for startup_data in startup_feedback_list:
            startup_name = startup_data.get('startup_name', 'Unknown')
            judges_feedback = startup_data.get('judges_feedback', [])
            
            # Track category-level scores across judges
            startup_category_scores = {category: [] for category in self.comprehensive_columns.keys()}
            
            # Process each judge's feedback separately
            for judge_idx, judge in enumerate(judges_feedback, 1):
                row_data = {
                    'Startup Name': startup_name,
                    'Judge Number': judge_idx,
                    'Overall Judge Score': 0
                }
                
                # Calculate scores for each category and subcategory
                overall_judge_scores = []
                
                for category, subcategories in self.comprehensive_columns.items():
                    category_key = category.lower().replace(' ', '_')
                    judge_detailed_scores = judge.get('detailed_scores', {}).get(category_key, {})
                    
                    # Calculate average for this category for this judge
                    category_scores = []
                    
                    # Process each subcategory for this judge
                    for subcat_idx, subcat in enumerate(subcategories):
                        col_name = f"{category} - {subcat}"
                        score = judge_detailed_scores.get(subcat_idx, 0)
                        row_data[col_name] = score
                        category_scores.append(score)
                        overall_judge_scores.append(score)
                    
                    # Average score for this category
                    if category_scores:
                        category_avg = round(np.mean(category_scores), 2)
                        row_data[f'{category} Overall Score'] = category_avg
                        startup_category_scores[category].append(category_avg)
                
                # Calculate overall judge score
                if overall_judge_scores:
                    row_data['Overall Judge Score'] = round(np.mean(overall_judge_scores), 2)
                
                # Add startup's overall performance metrics
                row_data['Startup Overall Score'] = round(row_data['Overall Judge Score'] / 10, 2)
                
                rankings_data.append(row_data)
            
            # Add startup-level category average scores
            for category, scores in startup_category_scores.items():
                if scores:
                    startup_avg_score = round(np.mean(scores), 2)
                    for row in rankings_data:
                        if row['Startup Name'] == startup_name:
                            row[f'Startup {category} Overall Score'] = startup_avg_score
        
        # Create DataFrame
        df = pd.DataFrame(rankings_data)

        # Sort by startup's overall score and then by judge number
        df = df.sort_values(['Startup Overall Score', 'Startup Name', 'Judge Number'], 
                            ascending=[False, True, True])

        # Add overall startup rank (based on average of all judges)
        startup_avg_scores = df.groupby('Startup Name')['Overall Judge Score'].mean().reset_index()
        startup_avg_scores = startup_avg_scores.sort_values('Overall Judge Score', ascending=False)
        startup_avg_scores['Startup Rank'] = range(1, len(startup_avg_scores) + 1)

        # Merge ranks back to the main dataframe
        df = df.merge(startup_avg_scores[['Startup Name', 'Startup Rank']], on='Startup Name', how='left')

        # Reorder columns to make it more readable
        columns_order = ['Startup Rank', 'Startup Name', 'Judge Number', 'Overall Judge Score', 'Startup Overall Score']
        
        # Add category-level overall scores to columns order
        category_overall_scores = [col for col in df.columns if col.startswith('Startup ') and col.endswith('Overall Score')]
        columns_order.extend(sorted(category_overall_scores))
        
        # Add detailed columns
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