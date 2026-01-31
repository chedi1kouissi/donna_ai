# ATB Relationship Copilot 🏦🤖

> **Hackathon Track:** Problem 3 (Decision-making, Profiling, Strategy)
> **Tech Stack:** Google ADK, Gemini 2.0 Flash, Python (Flask), Agent-to-Agent (A2A) Protocol

## 📖 Overview

The **ATB Relationship Copilot** is a multi-agent AI system designed to act as a "Super Secretary" for a Tunisian **Chargé de Clientèle Entreprises**. 

Instead of a generic chatbot, it is a **decision-support engine** that automates the rigorous pre-meeting analysis and post-meeting administrative work required in corporate banking. It acts as a bridge between raw data, BCT regulations, and strategic credit decisions.

## 🏗️ Architecture & Frameworks

The system follows a **Fan-Out / Fan-In** orchestration pattern, built on **Google’s Agent Development Kit (ADK)** patterns.

*   **Orchestrator**: Central brain that coordinates the workflow.
*   **LLM Engine**: **Gemini 2.0 Flash** (via `google-generativeai`) for reasoning, summary, and translation.
*   **Communication**: Implements the **A2A (Agent-to-Agent) Protocol** standard for interoperability.
*   **Backend**: Flask API exposing endpoints for the frontend/mobile app.

## 🤖 The Multi-Agent System

The system is composed of 5 specialized agents, each mirroring a specific banking role:

### 1. 🕵️ Data Retriever Agent (The "Analyst")
*   **Role**: Aggregates data from disparate sources (CRM, Core Banking, Legacy Systems).
*   **Key Innovation**: Automatically checks the **Centrale des Risques (BCT)** report.
*   **Output**: `NormalizedClientSnapshot` (Classifies debt as Class 0-4).

### 2. 📝 Client Brief Agent (The "Secretary")
*   **Role**: Prepares the formal **"Fiche de Visite"**.
*   **Task**: Replaces the generic "brief" with the specific format used in Tunisian banks (Objectif, Chiffres Clés, Impayés).
*   **Outcome**: A 1-page executive summary for the banker to read in the car.

### 3. ⚖️ Risk & Compliance Agent (The "Regulatory Brain")
*   **Role**: Checks every file against **Banque Centrale de Tunisie (BCT)** regulations.
*   **Special Tool**: `search_bct_regulations` (RAG-lite).
*   **Behavior**: Cites specific circulars (e.g., *Circular 2024-01*) when flagging risks (KYC, DSCR ratios).

### 4. 💡 Opportunity Agent (The "Credit Strategist")
*   **Role**: Prepares arguments for the **Credit Committee**.
*   **Special Tool**: `calculate_loan_payment` (Financial Simulator).
*   **Outcome**: Instead of a "sales pitch", it generates a **Credit Defense**:
    *   *Proposed Structure*: 80k TND / 48 months.
    *   *Financial Logic*: "Monthly payment (2,150 TND) fits within N-1 cash flow."
    *   *Mitigation*: "Guaranteed by SOTUGAR."

### 5. ✍️ After Meeting Agent (The "Admin")
*   **Role**: Finalizes the file after the visit.
*   **Task**: Converts rough notes into a formal **Compte-rendu de visite (Official Minutes)**.
*   **Automation**: Updates the `client_case.json` and drafts the follow-up email.

## 🛠️ Specialized Tools

Specific Python tools were built to ground the AI in reality:
*   `get_client_data(id)`: Loads realistic fixtures (CRM, Account Summary, Docs).
*   `search_bct_regulations(query)`: Searches a local knowledge base of banking circulars.
*   `calculate_loan_payment(amt, rate, dur)`: Deterministic PMT calculator for accurate simulations.
*   `get_product_catalog()`: Loads bank specific product rules.

## 📂 Project Structure

```bash
📦 donna_ai
├── 📄 app.py               # Main Flask API Server
├── 📄 agents.py            # Definition of 5 ADK Agents
├── 📄 orchestrator.py      # Business Logic & Workflow
├── 📄 tools.py             # Tools: BCT Search, Loan Calc, Data Loaders
├── 📄 schemas.py           # Pydantic Models (Strict JSON validation)
├── 📄 a2a_server.py        # A2A Protocol Implementation
├── 📂 data
│   ├── 📂 fake_clients     # Fixtures (ATB-SME-001)
│   ├── 📄 product_catalog.json
│   └── 📄 bct_knowledge_base.json # Banking Regulations
└── 📂 outputs              # Generated "Prep Packs" (Markdown)
```

## 🚀 How to Run

1.  **Install Requirements**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**
    *   Create `.env` file with your `GEMINI_API_KEY`.

3.  **Start Server**
    ```bash
    python app.py
    ```

4.  **Test Scenarios**
    *   **Generate Fiche de Visite**:
        ```powershell
        Invoke-RestMethod -Uri "http://localhost:5000/prep-pack" -Method Post -ContentType "application/json" -Body '{"client_id": "ATB-SME-001"}'
        ```
    *   **Post-Meeting Update**:
        ```powershell
        Invoke-RestMethod -Uri "http://localhost:5000/after-meeting" -Method Post -ContentType "application/json" -Body '{"client_id": "ATB-SME-001", "meeting_date": "2026-02-01", "meeting_type": "Visite", "banker_notes": ["Client agrees"]}'
        ```
