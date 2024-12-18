from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import openai
import os

# Initialize Flask app
app = Flask(__name__)

CORS(app) #origins=["http://localhost.com/123trapliften"])

# Set up OpenAI API key from an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")  # Store your API key securely as an environment variable

# Load JSON content from file (only once at startup)
try:
    with open("scriptQA.json", "r") as file:
        json_data = json.load(file)
        
        # Check JSON structure and assign content
        if "LiftScripts" in json_data:
            content = json.dumps(json_data["LiftScripts"])  # Convert to string if it's a dict or list
        else:
            raise KeyError("The JSON file must contain a 'LiftScripts' key at the root.")
except FileNotFoundError:
    print("The JSON file 'script.json' was not found.")
    content = ""
except KeyError as e:
    print(f"Key error: {e}")
    content = ""

# Initialize conversation history with a single system message containing the JSON content
conversation_history = [
    {
        "role": "system", 
        "content": (
            f"Ik wil dat je op basis van dit betand de klant helpt:\n\n{content}\n\n"
            "Probeer eerst te achterhalen welk type lift de klant heeft en ga dan stapsgewijs door het document om de klant verder te helpen."
            "Voor het achterhalen van het type kan je verwijzen naar de documentatie die ze hebben gekregen en naar de sticket op de stoel waar ook meestal het type op staat, anders gebruik je de kenmerken uit het script"
            "Houd de antwoorden kort, duidelijk en bondig, maar zorg ervoor dat ze gevoel van verbondenheid geven."
            "Zeg niet te vaak en te snel dat ze contact op moeten nemen met een monteur, mocht het wel moeten verwijs dan naar dit telefoon nummer: 085 303 6194."
            "Probeer alle antwoorden in goed nederlands zonder rare leestekens te geven."
             )
    }
]

# Maximum allowed messages in the conversation history to stay under token limit
MAX_HISTORY_LENGTH = 20  # Adjust as needed based on typical token usage

# Function to query OpenAI with conversation history
def query_with_memory(question):
    # Add the new user question to the conversation history
    conversation_history.append({"role": "user", "content": question})

    # Send the conversation history to OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history
    )

    # Get the assistant's answer
    answer = response.choices[0].message['content']

    # Append the assistant's answer to the conversation history
    conversation_history.append({"role": "assistant", "content": answer})

    # Check if the conversation history exceeds the maximum length
    while len(conversation_history) > MAX_HISTORY_LENGTH + 1:  # +1 for the initial system message
        # Remove the oldest user-assistant pair (ignoring the first system message)
        conversation_history.pop(1)  # Remove the oldest user message
        conversation_history.pop(1)  # Remove the corresponding assistant message

    return answer

# Define API route for chatbot queries
@app.route('/ask', methods=['POST'])
def ask_content():
    data = request.get_json()
    question = data.get('question')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    # Query with memory and get the answer
    answer = query_with_memory(question)
    
    return jsonify({"answer": answer})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
