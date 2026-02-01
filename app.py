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

@app.route('/client-update', methods=['POST'])
def client_update():
    """Handle informal client updates (calls, emails, doc received) without formal meeting."""
    try:
        data = request.json
        required_fields = ["client_id", "update_type", "message"]
        if not data or any(f not in data for f in required_fields):
            return jsonify({"error": f"Missing required fields: {required_fields}"}), 400
            
        client_id = data["client_id"]
        update_type = data["update_type"]  # e.g., "Call", "Email", "Document Received"
        message = data["message"]
        
        # Save directly to interactions log
        import datetime
        from tools import new_id
        log_path = os.path.join("data", "fake_clients", client_id, "interactions_log.json")
        
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []
            
        new_entry = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "type": update_type,
            "summary": message,
            "outcome": "Logged via chatbot."
        }
        logs.insert(0, new_entry)
        
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
            
        return jsonify({"success": True, "message": "Update logged successfully"}), 200
        
    except Exception as e:
        logger.error(f"Error in /client-update: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/create-reminder', methods=['POST'])
def create_reminder():
    """Create a future reminder for client."""
    try:
        data = request.json
        required_fields = ["client_id", "reminder_text", "due_date", "priority"]
        if not data or any(f not in data for f in required_fields):
            return jsonify({"error": f"Missing required fields: {required_fields}"}), 400
            
        client_id = data["client_id"]
        
        # Save to reminders file
        import datetime
        import json
        from tools import new_id
        reminders_path = os.path.join("data", "fake_clients", client_id, "reminders.json")
        
        if os.path.exists(reminders_path):
            with open(reminders_path, "r", encoding="utf-8") as f:
                reminders = json.load(f)
        else:
            reminders = []
            
        new_reminder = {
            "id": new_id("reminder"),
            "reminder_text": data["reminder_text"],
            "product_type": data.get("product_type", "General"),
            "due_date": data["due_date"],
            "priority": data["priority"],
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat(),
            "created_by": "Banker"
        }
        reminders.append(new_reminder)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(reminders_path), exist_ok=True)
        
        with open(reminders_path, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2)
            
        return jsonify({"success": True, "reminder": new_reminder}), 200
        
    except Exception as e:
        logger.error(f"Error in /create-reminder: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/get-reminders/<client_id>', methods=['GET'])
def get_reminders(client_id):
    """Get all reminders for a client."""
    try:
        import json
        reminders_path = os.path.join("data", "fake_clients", client_id, "reminders.json")
        
        if not os.path.exists(reminders_path):
            return jsonify({"reminders": []}), 200
            
        with open(reminders_path, "r", encoding="utf-8") as f:
            reminders = json.load(f)
            
        return jsonify({"reminders": reminders}), 200
        
    except Exception as e:
        logger.error(f"Error in /get-reminders: {e}", exc_info=True)
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
