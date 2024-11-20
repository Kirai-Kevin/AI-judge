import requests
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRankingsAPI:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.rankings_endpoint = f"{base_url}/rankings/download_rankings"

    def test_download_rankings(self, payload):
        """Test the rankings download endpoint with the given payload"""
        try:
            logger.info("Testing rankings download...")
            response = requests.post(self.rankings_endpoint, json=payload)
            response.raise_for_status()

            if response.headers.get('Content-Disposition'):
                filename = response.headers.get('Content-Disposition').split('filename=')[-1].strip('"')
                with open(filename, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Rankings file downloaded successfully: {filename}")
                return True, filename
            else:
                logger.error("No file received in response")
                return False, response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return False, str(e)

    def validate_payload(self, payload):
        """Validate the structure of the test payload"""
        try:
            required_score_categories = [
                "problem", "solution", "innovation", "team", 
                "business_model", "market_opportunity", 
                "technical_feasibility", "execution_strategy", "communication"
            ]

            for startup in payload["startup_feedback"]:
                if not startup.get("startup_name"):
                    raise ValueError("Missing startup name")
                
                if not startup.get("judges_feedback"):
                    raise ValueError(f"No judges feedback for {startup['startup_name']}")
                
                for judge_feedback in startup["judges_feedback"]:
                    scores = judge_feedback.get("scores", {})
                    missing_categories = [cat for cat in required_score_categories if cat not in scores]
                    if missing_categories:
                        raise ValueError(f"Missing score categories: {missing_categories}")
                    
                    if not judge_feedback.get("feedback"):
                        raise ValueError("Missing feedback text")

            return True, "Payload validation successful"
        except Exception as e:
            return False, str(e)

# Adjusted payload for testing
test_payload = {
    "startup_feedback": [
        {
            "startup_name": "InnovateX",
            "judges_feedback": [
                {
                    "scores": {
                        "problem": 8,
                        "solution": 7,
                        "innovation": 9,
                        "team": 8,
                        "business_model": 7,
                        "market_opportunity": 6,
                        "technical_feasibility": 8,
                        "execution_strategy": 7,
                        "communication": 7
                    },
                    "feedback": "Strong team but needs better communication of market opportunity."
                },
                {
                    "scores": {
                        "problem": 9,
                        "solution": 8,
                        "innovation": 9,
                        "team": 9,
                        "business_model": 8,
                        "market_opportunity": 7,
                        "technical_feasibility": 8,
                        "execution_strategy": 8,
                        "communication": 8
                    },
                    "feedback": "Excellent problem definition and solution, but refine execution strategy."
                },
                {
                    "scores": {
                        "problem": 8,
                        "solution": 7,
                        "innovation": 8,
                        "team": 8,
                        "business_model": 7,
                        "market_opportunity": 7,
                        "technical_feasibility": 7,
                        "execution_strategy": 7,
                        "communication": 6
                    },
                    "feedback": "Good potential but needs refinement in execution strategy."
                }
            ]
        },
        {
            "startup_name": "TechNova",
            "judges_feedback": [
                {
                    "scores": {
                        "problem": 7,
                        "solution": 6,
                        "innovation": 8,
                        "team": 7,
                        "business_model": 6,
                        "market_opportunity": 7,
                        "technical_feasibility": 6,
                        "execution_strategy": 7,
                        "communication": 6
                    },
                    "feedback": "Solid innovation but weak business model and communication."
                },
                {
                    "scores": {
                        "problem": 8,
                        "solution": 7,
                        "innovation": 7,
                        "team": 8,
                        "business_model": 7,
                        "market_opportunity": 8,
                        "technical_feasibility": 7,
                        "execution_strategy": 8,
                        "communication": 7
                    },
                    "feedback": "Improved communication but needs stronger business model."
                },
                {
                    "scores": {
                        "problem": 6,
                        "solution": 6,
                        "innovation": 7,
                        "team": 7,
                        "business_model": 6,
                        "market_opportunity": 6,
                        "technical_feasibility": 6,
                        "execution_strategy": 7,
                        "communication": 7
                    },
                    "feedback": "Decent execution but lacking in innovation and market opportunity."
                }
            ]
        },
        {
            "startup_name": "FutureTech",
            "judges_feedback": [
                {
                    "scores": {
                        "problem": 8,
                        "solution": 8,
                        "innovation": 9,
                        "team": 8,
                        "business_model": 8,
                        "market_opportunity": 8,
                        "technical_feasibility": 8,
                        "execution_strategy": 8,
                        "communication": 8
                    },
                    "feedback": "Well-rounded startup with excellent potential."
                },
                {
                    "scores": {
                        "problem": 9,
                        "solution": 9,
                        "innovation": 9,
                        "team": 9,
                        "business_model": 9,
                        "market_opportunity": 9,
                        "technical_feasibility": 9,
                        "execution_strategy": 9,
                        "communication": 9
                    },
                    "feedback": "Outstanding in all categories, a top performer."
                },
                {
                    "scores": {
                        "problem": 8,
                        "solution": 7,
                        "innovation": 8,
                        "team": 7,
                        "business_model": 7,
                        "market_opportunity": 7,
                        "technical_feasibility": 7,
                        "execution_strategy": 7,
                        "communication": 6
                    },
                    "feedback": "Good overall but needs stronger communication."
                }
            ]
        }
    ]
}

def main():
    # Initialize tester
    tester = TestRankingsAPI()
    
    # Validate payload first
    logger.info("Validating test payload...")
    is_valid, message = tester.validate_payload(test_payload)
    
    if not is_valid:
        logger.error(f"Payload validation failed: {message}")
        return
    
    # Run the test
    logger.info("Running rankings download test...")
    success, result = tester.test_download_rankings(test_payload)
    
    if success:
        logger.info("Test completed successfully!")
    else:
        logger.error(f"Test failed: {result}")

if __name__ == "__main__":
    main()
