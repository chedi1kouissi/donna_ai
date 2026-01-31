import os
import json
import random
import datetime
from config import Config

def get_client_data(client_id: str) -> dict:
    """Loads all fixture files for a client."""
    base_path = os.path.join(Config.FAKE_DATA_PATH, client_id)
    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Client data not found for {client_id} at {base_path}")

    data = {}
    files = [
        "crm_profile.json",
        "account_summary.json",
        "products_owned.json",
        "interactions_log.json",
        "document_vault_index.json",
        "client_case.json",
        "centrale_des_risques.json"
    ]

    for f in files:
        path = os.path.join(base_path, f)
        key = f.replace(".json", "")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                data[key] = json.load(file)
        else:
            data[key] = {} # Return empty dict if file missing
            
    return data

def get_product_catalog() -> list:
    """Loads product catalog."""
    path = Config.PRODUCT_CATALOG_PATH
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def new_id(prefix: str = "obj") -> str:
    """Generates a random ID."""
    return f"{prefix}_{random.randint(1000, 9999)}"

def reminder_dates(due_date_str: str) -> list:
    """Returns [due-1day, due] given a YYYY-MM-DD string."""
    try:
        due = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
        reminders = [
            (due - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            due.strftime("%Y-%m-%d")
        ]
        return reminders
    except ValueError:
        return []

def search_bct_regulations(query_keywords: list = None) -> list:
    """Simulates searching the local BCT knowledge base."""
    path = os.path.join("data", "bct_knowledge_base.json")
    # Handle absolute/relative path if needed, assuming run from root
    if not os.path.exists(path):
         # Try connecting to Config path location if that's safer
        path = os.path.join(Config.FAKE_DATA_PATH, "..", "bct_knowledge_base.json")
        if not os.path.exists(path):
            return []
            
    try:
        with open(path, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except:
        return []

    if not query_keywords:
        return kb

    results = []
    for item in kb:
        # naive match
        text = (item["title"] + " " + item["summary"]).lower()
        if any(k.lower() in text for k in query_keywords):
            results.append(item)
    return results

def calculate_loan_payment(amount: float, rate_percent: float, duration_months: int) -> float:
    """Calculates monthly payment (PMT)."""
    if duration_months <= 0 or amount <= 0:
        return 0.0
    if rate_percent <= 0:
        return amount / duration_months
        
    r = (rate_percent / 100) / 12
    # PMT = P * r * (1 + r)^n / ((1 + r)^n - 1)
    try:
        numerator = amount * r * ((1 + r) ** duration_months)
        denominator = ((1 + r) ** duration_months) - 1
        return round(numerator / denominator, 2)
    except:
        return 0.0

def get_standard_simulations() -> str:
    """Generates a cheat sheet of standard loan costs for the LLM."""
    scenarios = [
        (10000, 10, 36),
        (50000, 11, 48),
        (100000, 11, 60),
        (500000, 12, 60)
    ]
    txt = "Standard Loan Costs (Cheat Sheet):\n"
    for amt, rate, months in scenarios:
        pmt = calculate_loan_payment(amt, rate, months)
        txt += f"- {amt} TND @ {rate}% for {months}m = {pmt} TND/mo\n"
    return txt
