from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
import os
# Import CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST"])

# Initialize the OpenAI client with your API key and base URL
openai = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),  # Fetching the API key from environment variable
    base_url="https://cloud.olakrutrim.com/v1",  # Your AI vendor's base URL
)
# oPww47Zq2K5xQTUbo6jqZApi0H2tHl

# Define an endpoint to receive stock name and call AI for analysis
@app.route('/analyze_stock', methods=['POST'])
def analyze_stock():
    data = request.json
    stock_name = data.get('stock_name')

    # Construct the prompt using the stock name
    prompt = f"Give me a detailed analysis of the stock: {stock_name}"

    try:
        # Call the AI API with the constructed prompt
        chat_completion = openai.chat.completions.create(
            model="Meta-Llama-3-8B-Instruct",  # AI model from the vendor
            messages=[
                {"role": "system", "content": "You are a stock market analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            frequency_penalty=0,
            max_tokens=3000,
            n=1,
            temperature=0,
        )

        # Extract the AI's response
        analysis = chat_completion.choices[0].message.content

        # Return the response back to the frontend
        return jsonify({"stock_name": stock_name, "analysis": analysis})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
