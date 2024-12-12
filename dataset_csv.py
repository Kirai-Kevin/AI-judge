import json
import csv
import random
from datetime import datetime, timedelta

def generate_startup_evaluation():
    """Generate a realistic startup evaluation JSON with comprehensive details"""
    total_score = random.randint(60, 95)
    meet_startup = random.choice([True, False])
    mentor_startup = random.choice([True, False])
    nominate_next_round = total_score > 80

    # Team Section Detailed Generation
    team_section = {
        'rawAverage': round(random.uniform(3.0, 5.0), 1),
        'percentageScore': random.randint(60, 100),
        'weightedScore': random.randint(20, 35),
        'maxPoints': 40,
        'feedback': random.choice([
            "Strong leadership team",
            "Experienced and innovative group",
            "Solid team with diverse skills",
            "Promising team with growth potential"
        ]),
        'isSkipped': False,
        'individualScores': {
            'leadership': round(random.uniform(3.0, 5.0), 1),
            'experience': round(random.uniform(3.0, 5.0), 1)
        },
        'totalPossibleQuestions': 2,
        'answeredQuestions': 2
    }

    # Raw Form Data
    raw_form_data_team = {
        'scores': {
            'leadership': team_section['individualScores']['leadership'],
            'experience': team_section['individualScores']['experience']
        },
        'feedback': team_section['feedback'],
        'isSkipped': team_section['isSkipped']
    }

    evaluation = {
        'scoringTime': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat() + 'Z',
        'totalScore': total_score,
        'meetStartup': meet_startup,
        'mentorStartup': mentor_startup,
        'nominateNextRound': nominate_next_round,
        'overallFeedback': random.choice([
            "Strong potential with innovative solution",
            "Promising startup with clear vision",
            "Innovative approach with solid execution",
            "Demonstrating significant market potential"
        ]),
        'judgeId': f"{random.randint(100000, 999999)}",
        'startupId': f"{random.randint(100000, 999999)}",
        'roundId': f"{random.randint(100000, 999999)}",
        'sectionScores': {
            'teamSection': team_section
        },
        'rawFormData': {
            'teamSection': raw_form_data_team
        }
    }
    
    return evaluation

def convert_to_csv_row(evaluation):
    """Convert JSON evaluation to a single CSV row with specified structure"""
    team_section = evaluation['sectionScores']['teamSection']
    raw_form_team = evaluation['rawFormData']['teamSection']
    
    csv_row = {
        # Core evaluation metadata
        'scoringTime': evaluation['scoringTime'],
        'totalScore': evaluation['totalScore'],
        'meetStartup': evaluation['meetStartup'],
        'mentorStartup': evaluation['mentorStartup'],
        'nominateNextRound': evaluation['nominateNextRound'],
        'overallFeedback': evaluation['overallFeedback'],
        'judgeId': evaluation['judgeId'],
        'startupId': evaluation['startupId'],
        'roundId': evaluation['roundId'],
        
        # Team Section Detailed Metrics
        'teamSection_rawAverage': team_section['rawAverage'],
        'teamSection_percentageScore': team_section['percentageScore'],
        'teamSection_weightedScore': team_section['weightedScore'],
        'teamSection_maxPoints': team_section['maxPoints'],
        'teamSection_feedback': team_section['feedback'],
        'teamSection_isSkipped': team_section['isSkipped'],
        
        # Individual Scores
        'teamSection_individualScores_leadership': team_section['individualScores']['leadership'],
        'teamSection_individualScores_experience': team_section['individualScores']['experience'],
        
        # Questions Metrics
        'teamSection_totalPossibleQuestions': team_section['totalPossibleQuestions'],
        'teamSection_answeredQuestions': team_section['answeredQuestions'],
        
        # Raw Form Data
        'rawFormData_teamSection_scores_leadership': raw_form_team['scores']['leadership'],
        'rawFormData_teamSection_scores_experience': raw_form_team['scores']['experience'],
        'rawFormData_teamSection_feedback': raw_form_team['feedback'],
        'rawFormData_teamSection_isSkipped': raw_form_team['isSkipped']
    }
    
    return csv_row

def generate_dataset(num_samples=100, output_file='startup_evaluation_dataset.csv'):
    """Generate a dataset of startup evaluations with structured CSV"""
    all_rows = []
    
    # Generate samples
    for _ in range(num_samples):
        evaluation = generate_startup_evaluation()
        csv_row = convert_to_csv_row(evaluation)
        all_rows.append(csv_row)
    
    # Write to CSV
    if all_rows:
        keys = all_rows[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            dict_writer = csv.DictWriter(csvfile, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_rows)
    
    print(f"Dataset generated with {len(all_rows)} rows in {output_file}")
    print("Columns in the dataset:", ", ".join(keys))

# Generate the dataset
generate_dataset(num_samples=500)  # Increased to 500 samples for more comprehensive training