from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from orchestrator import Orchestrator
import logging

app = Flask(__name__)
CORS(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Orchestrator
orchestrator = Orchestrator()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "model": Config.GEMINI_MODEL,
        "data_mode": Config.DATA_MODE
    })

@app.route('/prep-pack', methods=['POST'])
def prep_pack():
    try:
        data = request.json
        if not data or "client_id" not in data:
            return jsonify({"error": "client_id is required"}), 400
            
        client_id = data["client_id"]
        language = data.get("language", "fr")
        
        result = orchestrator.build_prep_pack(client_id, language)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in /prep-pack: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/after-meeting', methods=['POST'])
def after_meeting():
    try:
        data = request.json
        required_fields = ["client_id", "meeting_date", "banker_notes"]
        if not data or any(f not in data for f in required_fields):
            return jsonify({"error": f"Missing required fields: {required_fields}"}), 400
            
        client_id = data["client_id"]
        
        result = orchestrator.update_case_after_meeting(client_id, data)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in /after-meeting: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting ATB Relationship Copilot Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
