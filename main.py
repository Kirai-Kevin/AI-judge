from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-pro')

async def generate_summary(feedback_list):
    """
    Summarize feedback using Gemini-Pro.
    """
    prompt = f"""
    Summarize the following feedback into three concise, actionable insights:
    Feedback:
    {feedback_list}
    Provide clear and constructive points.
    """

    try:
        # Generate content using the modern method
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(

            )
        )
        
        # Extract the text from the response
        return response.text
    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        return "Error generating summary. Please try again."

@app.route("/summarize_feedback", methods=["POST"])
async def summarize_feedback():
    """
    API endpoint to summarize judge feedback.
    """
    try:
        data = request.json
        feedback_list = data.get("feedback")
        
        if not feedback_list:
            return jsonify({"error": "No feedback provided."}), 400

        # Generate summary using Gemini-Pro
        summary = await generate_summary(feedback_list)
        return jsonify({"summary": summary}), 200

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

if __name__ == "__main__":
    # Run the Flask app with async support
    app.run(debug=True)



    from flask import Flask, request, jsonify
import anthropic
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure API keys and generative models
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

# Initialize Anthropic client
anthropic_client = anthropic.Client(api_key=anthropic_api_key)

# Logging
logging.basicConfig(level=logging.INFO)

# Summarization function
def generate_summary(feedback_list, use_claude=True):
    """
    Summarize feedback using Claude or Gemini-Pro as fallback.
    """
    prompt = f"""
    Summarize the following feedback into three concise, actionable insights:

    Feedback:
    {feedback_list}

    Provide clear and constructive points.
    """

    try:
        if use_claude:
            # Use Claude API
            response = anthropic_client.messages.create(
                model="claude-3",
                max_tokens=100,
                temperature=0.7,
                system="You are an expert summarizer for startup pitch feedback.",
                messages=[{"role": "user", "content": prompt}],
            )
            return response["content"]
        else:
            # Fallback to Gemini-Pro API
            response = genai.generate_text(
                model="gemini_pro",
                prompt=prompt,
                max_output_tokens=100,
                temperature=0.7,
            )
            return response.result

    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        return "Error generating summary. Please try again."

# Flask route
@app.route("/summarize_feedback", methods=["POST"])
def summarize_feedback():
    """
    API endpoint to summarize judge feedback.
    """
    try:
        data = request.json
        feedback_list = data.get("feedback")

        if not feedback_list:
            return jsonify({"error": "No feedback provided."}), 400

        # Generate summary using Claude with Gemini fallback
        try:
            summary = generate_summary(feedback_list, use_claude=True)
        except Exception as e:
            logging.warning(f"Claude failed: {e}. Falling back to Gemini.")
            summary = generate_summary(feedback_list, use_claude=False)

        return jsonify({"summary": summary}), 200

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
