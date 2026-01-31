from flask import Flask, request, jsonify
from config import Config
from agents import OpportunityAgent, RiskComplianceAgent
import logging

# Try to import A2A types if available
try:
    import google.adk.a2a as a2a
except ImportError:
    a2a = None

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("A2A_Server")

# Initialize agents
agents = {
    "opportunity_agent": OpportunityAgent(),
    "risk_compliance_agent": RiskComplianceAgent()
}

@app.route('/a2a/message', methods=['POST'])
def handle_message():
    """
    Handles A2A protocol messages.
    Adheres to the standard envelope structure found in google-adk a2a specifications.
    """
    try:
        envelope = request.json
        logger.info(f"Received A2A message: {envelope}")
        
        # Envelope Validation (Minimal)
        required_keys = ["message_id", "from_agent", "to_agent", "payload"]
        if not all(k in envelope for k in required_keys):
            return jsonify({"error": "Invalid A2A Envelope", "missing": required_keys}), 400

        target_agent_name = envelope.get("to_agent")
        if target_agent_name not in agents:
            return jsonify({"error": f"Agent {target_agent_name} not found"}), 404
            
        agent = agents[target_agent_name]
        payload = envelope.get("payload", {})
        
        # Execute Agent Logic
        try:
            # We map the A2A payload directly to the agent's run method kwargs
            # In a full ADK implementation, we might specificy the 'tool' or 'task' in the envelope
            result = agent.run(**payload)
            status = "success"
            output_payload = result
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            status = "error"
            output_payload = {"error": str(e)}

        # Construct Response Envelope
        response_envelope = {
            "message_id": f"{envelope.get('message_id')}_resp",
            "reply_to": envelope.get("message_id"),
            "from_agent": target_agent_name,
            "to_agent": envelope.get("from_agent"),
            "status": status,
            "payload": output_payload,
            "metadata": {
                "library": "google-adk",
                "version": "1.0-prototype"
            }
        }
        
        return jsonify(response_envelope), 200

    except Exception as e:
        logger.error(f"A2A Server Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"Starting A2A Server on port {Config.A2A_PORT}...")
    print(f"ADK Library Status: {'Available' if a2a else 'Not Found (Mocking Protocol)'}")
    app.run(host=Config.A2A_HOST, port=Config.A2A_PORT)
