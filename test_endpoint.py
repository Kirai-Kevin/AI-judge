import requests

# Define the payload
payload = {
    "startupId": "ST001",
    "teamName": "Innovative Tech Solutions",
    "scoringSections": [
        {
            "title": "Problem Definition",
            "score": 8.5,
            "weight": 0.2,
            "feedback": "Clear problem statement"
        },
        {
            "title": "Solution Approach",
            "score": 9.0,
            "weight": 0.3,
            "feedback": "Innovative solution design"
        }
    ],
    "generalFeedback": "Promising startup with strong potential",
    "totalScore": 8.75,
    "nominatedForNextRound": 2,
    "mentorInterest": 2,
    "heroesWantToMeet": 2,
    "rank": 1
}

# Send a POST request to the endpoint
response = requests.post('http://127.0.0.1:5000/summarize_feedback', json=payload)

# Print the response
print(response.status_code)
print(response.json())