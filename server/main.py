import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from langfuse import Langfuse
import traceback

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS for frontend requests
CORS(app)

print("=== INITIALIZATION ===")

# --- Initialize Langfuse ---
try:
    langfuse = Langfuse(
        secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
        public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
        host=os.environ.get("LANGFUSE_HOST"),
    )
    print("✅ Langfuse initialized successfully")
except Exception as e:
    print(f"❌ Langfuse initialization failed: {e}")
    langfuse = None

# --- Configure Google Gemini ---
gemini_api_key = os.environ.get("GEMINI_API_KEY")
if not gemini_api_key:
    print("❌ GEMINI_API_KEY not found in environment variables.")
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
else:
    print("✅ GEMINI_API_KEY found")

try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini model initialized successfully")
except Exception as e:
    print(f"❌ Gemini initialization failed: {e}")
    raise

print("=== SERVER STARTING =====")

@app.route('/api/generate-tweet', methods=['POST'])
def generate_tweet():
    """
    API endpoint to generate a tweet based on a topic.
    Includes Langfuse tracing for observability.
    """
    generation = None

    try:
        data = request.get_json()
        topic = data.get('topic') if data else None

        if not topic:
            print("❌ No topic provided")
            return jsonify({"error": "Topic is required"}), 400

        # --- CORRECTED FLOW: Use start_generation ---
        if langfuse:
            try:
                # This is the corrected method name based on your debug logs
                generation = langfuse.start_generation(
                    name="ai-tweet-writer",
                    user_id="user-123",
                    model="gemini-1.5-flash",
                    input={"topic": topic},
                )
            except Exception as e:
                print(f"⚠️ Langfuse generation creation failed: {e}")
                generation = None # Ensure generation is None if creation fails

        # --- Prepare prompt ---
        prompt = f"Generate a short, engaging, and professional tweet about the following topic: {topic}. Include 1-3 relevant hashtags."

        # --- Call the LLM ---
        try:
            response = model.generate_content(prompt)
        except Exception as e:
            print(f"❌ Gemini API call failed: {e}")
            if generation:
                generation.end(output={"error": "Gemini API call failed", "reason": str(e)})
            return jsonify({"error": f"AI service error: {str(e)}"}), 500

        # Robust check if the response was blocked or empty
        if not hasattr(response, 'parts') or not response.parts:
            reason = "Unknown reason"
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and hasattr(response.prompt_feedback, 'block_reason'):
                reason = response.prompt_feedback.block_reason.name
            
            print(f"❌ Gemini response was empty or blocked. Reason: {reason}")
            if generation:
                generation.end(output={"error": "Blocked or empty response", "reason": reason})
            return jsonify({"error": f"Content generation failed. Reason: {reason}"}), 400

        try:
            generated_text = response.text
        except Exception as e:
            print(f"❌ Failed to extract text from response: {e}")
            if generation:
                generation.end(output={"error": "Failed to extract text", "reason": str(e)})
            return jsonify({"error": "Failed to process AI response"}), 500

        # Update the Generation with the output and usage stats
        if generation:
            try:
                usage_data = response.usage_metadata if hasattr(response, 'usage_metadata') else None
                if usage_data:
                    generation.end(
                        output=generated_text,
                        usage={
                            "input": usage_data.prompt_token_count,
                            "output": usage_data.candidates_token_count
                        }
                    )
                else:
                    generation.end(output=generated_text)
            except Exception as e:
                print(f"⚠️ Failed to update Langfuse generation: {e}")

        return jsonify({"tweet": generated_text})

    except Exception as e:
        print(f"❌ Unexpected error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        
        # Log error to Langfuse if available
        if langfuse and generation:
            try:
                # Use create_event and associate it with the correct trace
                langfuse.create_event(
                    name="error", 
                    level="ERROR", 
                    message=str(e),
                    trace_id=generation.trace_id # Get trace_id from the generation
                )
            except Exception as langfuse_error:
                print(f"⚠️ Failed to log error to Langfuse: {langfuse_error}")
        
        return jsonify({"error": "An unexpected server error occurred"}), 500
    
    finally:
        # Ensure that all buffered data is sent to Langfuse
        if langfuse:
            try:
                langfuse.flush()
            except Exception as e:
                print(f"⚠️ Failed to flush Langfuse: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "gemini_configured": bool(os.environ.get("GEMINI_API_KEY")),
        "langfuse_configured": bool(langfuse)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

