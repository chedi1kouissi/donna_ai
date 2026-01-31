from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Core Entities ---

class Task(BaseModel):
    id: str
    description: str
    status: str = Field(description="pending, in_progress, done")
    due_date: Optional[str] = None
    priority: str = Field(description="high, medium, low")

class Reminder(BaseModel):
    id: str
    trigger_date: str
    message: str
    linked_task_id: Optional[str] = None

# --- Agent 1: Data Retriever ---

class CentraleDesRisques(BaseModel):
    total_commitment_market: float
    worst_class: int = Field(description="0=Saine, 1=Surveiller, 2=Incertain, 3=Préoccupant, 4=Compromis")
    unpaid_amount: float
    bct_notes: str

class NormalizedClientSnapshot(BaseModel):
    client_id: str
    company_name: str
    segment: str
    crm_data: Dict[str, Any]
    financial_summary: Dict[str, Any]
    products_held: List[Dict[str, Any]]
    recent_interactions: List[Dict[str, Any]]
    document_status: Dict[str, Any]
    centrale_risques: Optional[CentraleDesRisques] = None
    missing_data: List[str] = Field(default_factory=list)

# --- Agent 2: Client Brief (Refined as Fiche de Visite) ---

class FicheDeVisiteResult(BaseModel):
    objet_visite: str
    synthese_situation: str
    chiffres_cles: Dict[str, str] = Field(description="CA N, CA N-1, Engagement Total, Impayés")
    points_vigilance: List[str]
    agenda_rencontre: List[str]
    questions_decouverte: List[str]
    
# --- Agent 3: Risk & Compliance ---

class RiskFlag(BaseModel):
    risk_type: str
    description: str
    severity: str = Field(description="high, medium, low")
    impact: str
    circular_reference: Optional[str] = None

class RiskComplianceResult(BaseModel):
    risk_flags: List[RiskFlag]
    verification_checklist: List[str]
    do_not_do_list: List[str]
    compliance_notes: str
    requires_human_approval: bool = True

# --- Agent 4: Opportunity ---

class CreditCommitteeArgument(BaseModel):
    product_name: str
    amount_proposal: Optional[str]
    purpose: str
    financial_justification: str
    mitigation_factors: str
    estimated_revenue: str

class OpportunityPlanResult(BaseModel):
    recommended_structure: List[CreditCommitteeArgument]
    quick_checklist: List[str]
    next_actions: List[Task]
    missing_data: List[str]

# --- Agent 5: After Meeting ---

class AfterMeetingResult(BaseModel):
    compte_rendu_officiel: str = Field(description="Formal minutes for bank records")
    updated_tasks: List[Task]
    draft_email_subject: str
    draft_email_body: str
    new_reminders: List[Reminder]
    action_committee_required: bool

# --- Orchestrator Output ---

class PrepPack(BaseModel):
    snapshot: NormalizedClientSnapshot
    fiche_visite: FicheDeVisiteResult
    risk_assessment: RiskComplianceResult
    opportunities: OpportunityPlanResult
    generated_at: str
