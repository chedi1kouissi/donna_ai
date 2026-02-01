"""
Conversational Agent for Natural Language Command Execution
Handles intent detection, slot filling, and action execution through dialog.
"""
import json
import logging
from typing import Dict, Any, Optional
from config import Config
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ConversationAgent:
    """Smart agent that understands banker commands and executes actions through dialog."""
    
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        
    def process_message(self, user_message: str, conversation_history: list, conversation_state: dict) -> dict:
        """
        Process user message and determine next action.
        Returns: {
            "response": "Agent's reply to user",
            "action": "generate_prep_pack|create_reminder|log_update|submit_notes|none",
            "params": {...},  # Parameters for action (if complete)
            "missing_slots": [...],  # What's still needed
            "state": {...}  # Updated conversation state
        }
        """
        logger.info(f"Processing message: {user_message[:100]}...")
        
        # Build conversation context
        context = self._build_context(conversation_history, conversation_state)
        
        # Create prompt for intent detection and slot filling
        prompt = f"""You are an AI assistant for a Tunisian banker. Analyze the user's message and determine their intent.

Available actions:
1. generate_prep_pack: Generate a client briefing (needs: client_id)
2. create_reminder: Set a future reminder (needs: client_id, reminder_text, due_date, priority)
3. log_update: Log informal client update (needs: client_id, update_type, message)
4. submit_notes: Submit formal meeting notes (needs: client_id, meeting_date, meeting_type, notes)

Current conversation state: {json.dumps(conversation_state, indent=2)}
Recent messages: {json.dumps(conversation_history[-3:], indent=2)}

User's message: "{user_message}"

Instructions:
1. Detect the user's intent (which action they want)
2. Extract any mentioned parameters (client name/ID, dates, priorities, etc.)
3. Identify missing required parameters
4. Generate a natural, helpful response in English

If client name is mentioned (e.g., "SOTUPLAST"), map it to client_id: "ATB-SME-001".

Respond ONLY with valid JSON:
{{
    "intent": "action_name or none",
    "extracted_params": {{}},
    "missing_slots": [],
    "response": "Your natural language response to the user in English",
    "reasoning": "Brief explanation of your analysis"
}}"""

        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            
            # Update conversation state
            if result.get("intent") != "none":
                conversation_state["intent"] = result["intent"]
                conversation_state.setdefault("collected_params", {}).update(result.get("extracted_params", {}))
            
            # Check if we have all required params
            action_ready = False
            params = conversation_state.get("collected_params", {})
            missing = result.get("missing_slots", [])
            
            if result["intent"] != "none" and not missing:
                action_ready = True
            
            return {
                "response": result["response"],
                "action": result["intent"] if action_ready else "none",
                "params": params if action_ready else {},
                "missing_slots": missing,
                "state": conversation_state,
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "response": "Sorry, I didn't understand. Could you rephrase your request?",
                "action": "none",
                "params": {},
                "missing_slots": [],
                "state": conversation_state
            }
    
    def _build_context(self, history: list, state: dict) -> str:
        """Build context string from conversation history."""
        if not history:
            return "New conversation"
        
        context_lines = []
        for msg in history[-5:]:  # Last 5 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
