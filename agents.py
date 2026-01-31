import google.generativeai as genai
import json
import logging
from config import Config
from schemas import (
    NormalizedClientSnapshot, FicheDeVisiteResult, RiskComplianceResult,
    OpportunityPlanResult, AfterMeetingResult
)
from tools import (
    get_client_data, get_product_catalog, new_id, reminder_dates,
    search_bct_regulations, get_standard_simulations
)

# Import Google ADK
try:
    from google.adk import Agent as AdkAgent
except ImportError:
    # Fallback if library issue, but we expect it to be there
    logging.warning("google.adk not found, using valid mock for local run")
    class AdkAgent:
        def __init__(self, name=None):
            self.name = name

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Gemini
try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Gemini: {e}")

class BaseAgent(AdkAgent):
    """
    Wrapper combining Google ADK Agent structure with Gemini 2.0 Flash reasoning.
    """
    def __init__(self, name: str, model_name: str = Config.GEMINI_MODEL):
        super().__init__(name=name)
        self.model = genai.GenerativeModel(model_name)
        
    def generate(self, prompt: str, schema_class) -> dict:
        """Generates content and attempts to parse it as strict JSON matching the schema."""
        logger.info(f"Agent {self.name} invoked.")
        
        full_prompt = (
            f"You are the {self.name}. \n"
            f"Your output must be strict JSON adhering to the following schema:\n"
            f"{schema_class.model_json_schema()}\n"
            f"Important: Do not output markdown blocks like ```json ... ```. Just the raw JSON string.\n\n"
            f"Task:\n{prompt}"
        )

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2, # Low temp for factual/structured output
                    response_mime_type="application/json" 
                )
            )
            
            # Helper to clean markdown if present
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            data = json.loads(text)
            
            # Validate with Pydantic
            validated_obj = schema_class(**data)
            logger.info(f"Agent {self.name} finished successfully.")
            return validated_obj.model_dump()
            
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {e}")
            raise e

class DataRetrieverAgent(BaseAgent):
    def __init__(self):
        super().__init__("data_retriever_agent")

    def run(self, client_id: str) -> dict:
        data = get_client_data(client_id)
        prompt = (
            f"Normalize the raw client data for {client_id} into a clean snapshot.\n"
            f"Raw Data:\n{json.dumps(data, indent=2)}\n"
            f"Instructions:\n"
            f"- Extract key CRM info, financial summary (metrics), products active, and recent interaction summaries.\n"
            f"- Include 'centrale_risques' data if available (this is CRITICAL).\n"
            f"- Identify any critical missing documents.\n"
            f"- Do NOT halluncinate data. If missing, leave empty or note in 'missing_data'."
        )
        return self.generate(prompt, NormalizedClientSnapshot)

class ClientBriefAgent(BaseAgent):
    def __init__(self):
        super().__init__("client_brief_agent")

    def run(self, snapshot: dict) -> dict:
        prompt = (
            f"Act as a Chargé de Clientèle. Prepare the 'Fiche de Visite'.\n"
            f"Snapshot:\n{json.dumps(snapshot, indent=2)}\n"
            f"Instructions:\n"
            f"- 'objet_visite': Define the clear goal (e.g., 'Renouvellement dossier', 'Prospection').\n"
            f"- 'chiffres_cles': Extract CA, Total Engagement, and Impayés (from BCT report).\n"
            f"- 'points_vigilance': Highlight expired docs or BCT anomalies.\n"
            f"- 'agenda_rencontre': Steps for the meeting.\n"
            f"- 'questions_decouverte': Sales questions."
        )
        return self.generate(prompt, FicheDeVisiteResult)

class RiskComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__("risk_compliance_agent")

    def run(self, snapshot: dict, brief: dict) -> dict:
        # Retrieve relevant circulars (naive search based on snapshot segment or keywords)
        # In a real app we'd extract keywords first. Here we dump all for context.
        regulations = search_bct_regulations([]) 
        
        prompt = (
            f"Analyze risk and compliance methodology.\n"
            f"Snapshot:\n{json.dumps(snapshot, indent=2)}\n"
            f"Brief:\n{json.dumps(brief, indent=2)}\n"
            f"Relevant BCT Regulations:\n{json.dumps(regulations, indent=2)}\n"
            f"Instructions:\n"
            f"- Flag risks (KYC, financial, behavioral).\n"
            f"- CITE specific BCT Circulars in your risk flags if applicable.\n"
            f"- Create a strict verification checklist.\n"
            f"- List DO NOT DO actions (guardrails).\n"
            f"- Set requires_human_approval to true."
        )
        return self.generate(prompt, RiskComplianceResult)

class OpportunityAgent(BaseAgent):
    def __init__(self):
        super().__init__("opportunity_agent")

    def run(self, snapshot: dict, brief: dict) -> dict:
        catalog = get_product_catalog()
        simulations = get_standard_simulations()
        
        prompt = (
            f"Act as a Credit Analyst. Prepare arguments for the Credit Committee.\n"
            f"Snapshot:\n{json.dumps(snapshot, indent=2)}\n"
            f"Catalog:\n{json.dumps(catalog, indent=2)}\n"
            f"Financial Cheat Sheet:\n{simulations}\n"
            f"Fiche Visite Summary: {brief.get('synthese_situation')}\n"
            f"Instructions:\n"
            f"- Propose a credit structure (Amount, Purpose).\n"
            f"- JUSTIFY the proposal using financial logic (Cash flow vs Repayment).\n"
            f"- Mention 'Mitigation Factors' for any risks.\n"
            f"- Use 'CreditCommitteeArgument' structure."
        )
        return self.generate(prompt, OpportunityPlanResult)

class AfterMeetingAgent(BaseAgent):
    def __init__(self):
        super().__init__("after_meeting_agent")

    def run(self, banker_notes: list, client_id: str, meeting_date: str) -> dict:
        prompt = (
            f"Act as a Secretary. Finalize the file after the visit.\n"
            f"Client ID: {client_id}\n"
            f"Date: {meeting_date}\n"
            f"Notes:\n{json.dumps(banker_notes, indent=2)}\n"
            f"Instructions:\n"
            f"- Write a formal 'Compte-rendu de visite' (Official Minutes).\n"
            f"- List specific tasks (Recuperer bilan, Signer contrats).\n"
            f"- Draft email to client.\n"
            f"- Determine if action_committee_required (if new credit requested)."
        )
        return self.generate(prompt, AfterMeetingResult)
