import os
import sys
import json
import pandas as pd
import numpy as np

class StartupRankingProcessor:
    def __init__(self, api_key=None):
        self.category_weights = {
            'problem': 0.15,
            'solution': 0.15,
            'innovation': 0.12,
            'team': 0.12
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
            ]
        }

    def process_rankings(self, startup_feedback_list, comprehensive=True):
        return self._process_comprehensive_rankings(startup_feedback_list)

    def _process_comprehensive_rankings(self, startup_feedback_list):
        rankings_data = []
        
        for startup_data in startup_feedback_list:
            startup_name = startup_data.get('startup_name', 'Unknown')
            judges_feedback = startup_data.get('judges_feedback', [])
            
            for judge_idx, judge in enumerate(judges_feedback, 1):
                row_data = {
                    'Startup Name': startup_name,
                    'Judge Number': judge_idx,
                    'Overall Judge Score': 0
                }
                
                overall_judge_scores = []
                
                for category, subcategories in self.comprehensive_columns.items():
                    category_key = category.lower().replace(' ', '_')
                    judge_detailed_scores = judge.get('detailed_scores', {}).get(category_key, {})
                    
                    for subcat_idx, subcat in enumerate(subcategories):
                        col_name = f"{category} - {subcat}"
                        score = judge_detailed_scores.get(str(subcat_idx), 0)
                        row_data[col_name] = score
                        overall_judge_scores.append(score)
                
                if overall_judge_scores:
                    row_data['Overall Judge Score'] = round(np.mean(overall_judge_scores), 2)
                
                row_data['Startup Overall Score'] = round(row_data['Overall Judge Score'] / 10, 2)
                
                rankings_data.append(row_data)
        
        df = pd.DataFrame(rankings_data)
        
        df = df.sort_values(['Startup Overall Score', 'Startup Name', 'Judge Number'], 
                            ascending=[False, True, True])
        
        startup_avg_scores = df.groupby('Startup Name')['Overall Judge Score'].mean().reset_index()
        startup_avg_scores = startup_avg_scores.sort_values('Overall Judge Score', ascending=False)
        startup_avg_scores['Startup Rank'] = range(1, len(startup_avg_scores) + 1)
        
        df = df.merge(startup_avg_scores[['Startup Name', 'Startup Rank']], on='Startup Name', how='left')
        
        columns_order = ['Startup Rank', 'Startup Name', 'Judge Number', 'Overall Judge Score', 'Startup Overall Score']
        detailed_columns = [col for col in df.columns if col not in columns_order]
        columns_order.extend(sorted(detailed_columns))
        
        df = df[columns_order]
        
        return df

def main():
    # Load the test data
    with open('startup_feedback_test.json', 'r') as f:
        data = json.load(f)
    
    # Create rankings processor
    processor = StartupRankingProcessor()
    
    # Process rankings
    comprehensive_rankings = processor.process_rankings(data['startup_feedback'])
    
    # Save to CSV
    comprehensive_rankings.to_csv('comprehensive_startup_rankings.csv', index=False)
    print("Comprehensive rankings CSV generated successfully!")

if __name__ == '__main__':
    main()