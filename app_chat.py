import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- UPDATED IMPORTS ---
# We now only need to import the router function and potentially get_last_story
from story_engine import (
    handle_user_message,
    get_last_story # Kept for potential external checks, though not strictly required for the new router logic
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/chat", methods=["POST"])
def chat():
    """
    Handles all user messages (new story, refinement, or chat) using the 
    single entry point: handle_user_message.
    """
    data = request.get_json(force=True) or {}
    session_id = data.get("session", "default-session").strip()
    user_msg = (data.get("message") or "").strip()

    if not user_msg:
        return jsonify({"type": "chat", "reply": "Please send a message or a request for a story!"}), 200

    try:
        # The router function handles intent detection and execution internally
        response, response_type, revisions = handle_user_message(session_id, user_msg)

        if response_type == "story" or response_type == "refusal":
            # New story generation result (or refusal)
            return jsonify({
                "type": "story",
                "story": response,
                # Revisions will be 0 or 1, indicating if the internal judge forced a rewrite
                "internal_revisions": revisions,
                "status": response_type # "story" or "refusal"
            })

        elif response_type == "refinement":
            # Story refinement result
            return jsonify({
                "type": "refined",
                "story": response # This is the newly refined story text
            })

        else: # response_type == "chat"
            # Simple chat reply result
            return jsonify({
                "type": "chat",
                "reply": response
            })

    except Exception as e:
        # Log the error on the server side
        print(f"An error occurred in the chat endpoint: {e}")
        return jsonify({"type": "error", "error": f"An internal server error occurred: {str(e)}"}), 500


@app.route("/health")
def health():
    return {"ok": True}

if __name__ == "__main__":
    # Ensure all components are loaded before running the app
    # (The imports handle this)
    app.run(debug=True)
