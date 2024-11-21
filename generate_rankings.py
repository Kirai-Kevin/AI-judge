import os
import sys
import json
import pandas as pd
import numpy as np
from typing import List, Dict

class StartupRankingProcessor:
    def __init__(self, api_key=None):
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

    def calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted score based on category weights"""
        total_score = 0
        for category, score in scores.items():
            if category in self.category_weights:
                total_score += score * self.category_weights[category]
        return round(total_score, 2)

    def process_rankings(self, startup_feedback_list: List[Dict], comprehensive: bool = True) -> pd.DataFrame:
        """Process startup feedback and create rankings"""
        if comprehensive:
            return self._process_comprehensive_rankings(startup_feedback_list)
        else:
            return self._process_summary_rankings(startup_feedback_list)

    def _process_summary_rankings(self, startup_feedback_list: List[Dict]) -> pd.DataFrame:
        """Process summary rankings with startup and judge IDs"""
        rankings_data = []
        
        for startup_data in startup_feedback_list:
            startup_id = startup_data.get('startup_id')
            if not startup_id:
                continue  # Skip entries without startup_id
                
            startup_name = startup_data.get('startup_name', 'Unknown')
            judges_feedback = startup_data.get('judges_feedback', [])
            
            # Count nominations and interest
            nomination_count = sum(1 for judge in judges_feedback if judge.get('nominated_for_next_round', False))
            mentor_interest_count = sum(1 for judge in judges_feedback if judge.get('mentor_interest', False))
            hero_meetings_count = sum(1 for judge in judges_feedback if judge.get('hero_want_to_meet', False))
            
            # Prepare aggregated scores dictionary
            aggregated_scores = {category: 0 for category in self.category_weights.keys()}
            
            valid_judges = [judge for judge in judges_feedback if judge.get('judge_id')]
            if not valid_judges:
                continue
            
            for category in aggregated_scores.keys():
                scores = [judge.get('scores', {}).get(category, 0) for judge in valid_judges]
                aggregated_scores[category] = round(np.mean(scores), 2) if scores else 0
            
            # Calculate weighted score
            weighted_score = self.calculate_weighted_score(aggregated_scores)
            
            # Format nomination and interest counts
            nomination_col = nomination_count if nomination_count > 0 else False
            mentor_interest_col = mentor_interest_count if mentor_interest_count > 0 else False
            hero_meetings_col = hero_meetings_count if hero_meetings_count > 0 else False
            
            # Prepare ranking entry
            ranking_entry = {
                'Startup ID': startup_id,
                'Startup Name': startup_name,
                'Overall Score': weighted_score,
                'Nominated for Next Round': nomination_col,
                'Mentor Interest': mentor_interest_col,
                'Heroes Want to Meet': hero_meetings_col,
                'Rank': None,
                **aggregated_scores
            }
            
            rankings_data.append(ranking_entry)
        
        # Create DataFrame and sort
        df = pd.DataFrame(rankings_data)
        if not df.empty:
            df = df.sort_values('Overall Score', ascending=False)
            df['Rank'] = range(1, len(df) + 1)
        
        return df

    def _process_comprehensive_rankings(self, startup_feedback_list: List[Dict]) -> pd.DataFrame:
        """Process comprehensive rankings with startup and judge IDs"""
        rankings_data = []

        for startup_data in startup_feedback_list:
            startup_id = startup_data.get('startup_id')
            if not startup_id:
                continue  # Skip entries without startup_id
                
            startup_name = startup_data.get('startup_name', 'Unknown')
            judges_feedback = startup_data.get('judges_feedback', [])
            
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
                        # Handle both string and integer keys in detailed_scores
                        score = judge_detailed_scores.get(subcat_idx, judge_detailed_scores.get(str(subcat_idx), 0))
                        row_data[col_name] = score
                        category_scores.append(score)
                        overall_judge_scores.append(score)
                    
                    if category_scores:
                        category_avg = round(np.mean(category_scores), 2)
                        row_data[f'{category} Overall Score'] = category_avg
                
                if overall_judge_scores:
                    row_data['Overall Judge Score'] = round(np.mean(overall_judge_scores), 2)
                
                row_data['Startup Overall Score'] = round(row_data['Overall Judge Score'] / 10, 2)
                
                rankings_data.append(row_data)
        
        # Create DataFrame
        df = pd.DataFrame(rankings_data)
        
        if not df.empty:
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

def main():
    """Main function to test the ranking processor"""
    # Check if input file is provided as command line argument
    input_file = 'startup_feedback_test.json'
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    # Ensure input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        sys.exit(1)
    
    try:
        # Load the test data
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Create rankings processor
        processor = StartupRankingProcessor()
        
        # Process both types of rankings
        comprehensive_rankings = processor.process_rankings(data['startup_feedback'], comprehensive=True)
        summary_rankings = processor.process_rankings(data['startup_feedback'], comprehensive=False)
        
        # Generate timestamp for filenames
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        
        # Save to CSV files
        comprehensive_filename = f'comprehensive_startup_rankings_{timestamp}.csv'
        summary_filename = f'summary_startup_rankings_{timestamp}.csv'
        
        comprehensive_rankings.to_csv(comprehensive_filename, index=False)
        summary_rankings.to_csv(summary_filename, index=False)
        
        print(f"Rankings generated successfully!")
        print(f"Comprehensive rankings saved to: {comprehensive_filename}")
        print(f"Summary rankings saved to: {summary_filename}")
        
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{input_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing rankings: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()