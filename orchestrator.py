import json
import os
import datetime
import logging
from agents import (
    DataRetrieverAgent, ClientBriefAgent, RiskComplianceAgent, 
    OpportunityAgent, AfterMeetingAgent
)
from schemas import PrepPack, Task, Reminder
from config import Config
from tools import new_id

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.data_agent = DataRetrieverAgent()
        self.brief_agent = ClientBriefAgent()
        self.risk_agent = RiskComplianceAgent()
        self.opp_agent = OpportunityAgent()
        self.after_agent = AfterMeetingAgent()
        
        # Ensure outputs dir exists
        os.makedirs("outputs", exist_ok=True)

    def build_prep_pack(self, client_id: str, language: str = "fr"):
        logger.info(f"Building Prep Pack for {client_id}")
        
        # 1. Retrieve Data
        snapshot_data = self.data_agent.run(client_id)
        
        # 2. Generate Brief
        brief_data = self.brief_agent.run(snapshot_data)
        
        # 3. Assess Risk
        risk_data = self.risk_agent.run(snapshot_data, brief_data)
        
        # 4. Identify Opportunities
        opp_data = self.opp_agent.run(snapshot_data, brief_data)
        
        # 5. Assemble Prep Pack
        prep_pack = PrepPack(
            snapshot=snapshot_data,
            fiche_visite=brief_data,
            risk_assessment=risk_data,
            opportunities=opp_data,
            generated_at=datetime.datetime.now().isoformat()
        )
        
        # 6. Generate Markdown Report
        report_md = self._generate_markdown_report(prep_pack, client_id)
        
        # 7. Save Report
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"outputs/prep_pack_{client_id}_{date_str}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_md)
            
        return {
            "prep_pack": prep_pack.model_dump(),
            "report_markdown": report_md,
            "report_path": filename
        }

    def _update_interactions_log(self, client_id: str, meeting_date: str, meeting_type: str, summary: str):
        """Appends the new meeting to the interactions log so next PrepPack sees it."""
        log_path = os.path.join(Config.FAKE_DATA_PATH, client_id, "interactions_log.json")
        if not os.path.exists(log_path):
            return

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
            
            # Prepend new interaction
            new_entry = {
                "date": meeting_date,
                "type": meeting_type,
                "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                "outcome": "See Client Case for full minutes."
            }
            logs.insert(0, new_entry)
            
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update interactions log: {e}")

    def _update_document_vault(self, client_id: str, minutes: str):
        """Simple heuristic to update doc status if mentioned in minutes."""
        vault_path = os.path.join(Config.FAKE_DATA_PATH, client_id, "document_vault_index.json")
        if not os.path.exists(vault_path):
            return

        lower_minutes = minutes.lower()
        if "reçu" not in lower_minutes and "received" not in lower_minutes:
            return

        try:
            with open(vault_path, "r", encoding="utf-8") as f:
                vault = json.load(f)

            updated = False
            # heuristic: check for financial statements
            if "états financiers" in lower_minutes or "financial statements" in lower_minutes:
                for doc in vault.get("financial_docs", []):
                     if "2025" in doc.get("doc_name", ""):
                        doc["status"] = "Valid (Received)"
                        updated = True
            
            if updated:
                 with open(vault_path, "w", encoding="utf-8") as f:
                    json.dump(vault, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to update doc vault: {e}")

    def update_case_after_meeting(self, client_id: str, input_data: dict):
        logger.info(f"Updating case for {client_id}")
        
        # 1. Process Notes
        result_data = self.after_agent.run(
            banker_notes=input_data.get("banker_notes", []),
            client_id=client_id,
            meeting_date=input_data.get("meeting_date")
        )
        
        # 2. Update Case File
        case_path = os.path.join(Config.FAKE_DATA_PATH, client_id, "client_case.json")
        if os.path.exists(case_path):
            with open(case_path, "r", encoding="utf-8") as f:
                case_file = json.load(f)
        else:
            case_file = {"client_id": client_id, "case_history": [], "current_tasks": []}
            
        # Merge new data
        case_file["case_history"].append({
            "date": input_data.get("meeting_date"),
            "type": input_data.get("meeting_type"),
            "minutes": result_data["compte_rendu_officiel"],
            "draft_email": {
                "subject": result_data["draft_email_subject"],
                "body": result_data["draft_email_body"]
            }
        })
        
        # Add new tasks
        existing_tasks = case_file.get("current_tasks", [])
        for t in result_data["updated_tasks"]:
            # naive check to avoid dups based on description, ideally strictly new IDs
            t["id"] = new_id("task")
            existing_tasks.append(t)
        case_file["current_tasks"] = existing_tasks
        
        
        # Save
        with open(case_path, "w", encoding="utf-8") as f:
            json.dump(case_file, f, indent=2, default=str)
        
        # 3. Close the loop: Update Interactions Log for next Prep Pack
        self._update_interactions_log(
            client_id, 
            input_data.get("meeting_date"), 
            input_data.get("meeting_type"), 
            result_data["compte_rendu_officiel"]
        )
        
        # 4. Document Radar: Update Vault if docs received
        self._update_document_vault(client_id, result_data["compte_rendu_officiel"])
            
        return result_data

    def _generate_markdown_report(self, pack: PrepPack, client_id: str) -> str:
        s = pack.snapshot
        b = pack.fiche_visite # was brief
        r = pack.risk_assessment
        o = pack.opportunities
        
        md = f"# Client Prep Pack: {s.company_name} ({client_id})\n\n"
        md += f"**Date:** {pack.generated_at[:10]} | **Segment:** {s.segment}\n\n"
        
        md += "## 1. Fiche de Visite (Executive Brief)\n"
        md += f"**Objet:** {b.objet_visite}\n\n"
        md += f"{b.synthese_situation}\n\n"
        md += "**Chiffres Clés:**\n"
        for k, v in b.chiffres_cles.items():
            md += f"- **{k}:** {v}\n"
            
        md += "\n## 2. Risk & Compliance\n"
        if r.requires_human_approval:
            md += "> [!WARNING]\n> Human Verification Required\n\n"
        
        md += "**Flags:**\n"
        for flag in r.risk_flags:
            ref = f" (Ref: {flag.circular_reference})" if flag.circular_reference else ""
            md += f"- [{flag.severity.upper()}] {flag.risk_type}: {flag.description} (Impact: {flag.impact}){ref}\n"
            
        md += "\n## 3. Credit Committee Proposals\n"
        for opt in o.recommended_structure:
            md += f"### {opt.product_name} ({opt.amount_proposal or 'TBD'})\n"
            md += f"**Purpose:** {opt.purpose}\n"
            md += f"**Financial Logic:** {opt.financial_justification}\n"
            md += f"**Mitigation:** {opt.mitigation_factors}\n\n"
            
        md += "\n## 4. Meeting Agenda & Questions\n"
        for item in b.agenda_rencontre:
            md += f"- {item}\n"
            
        md += "\n**Questions Découverte:**\n"
        for q in b.questions_decouverte:
            md += f"- {q}\n"
            
        return md
