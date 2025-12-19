import requests
import time
import json

BASE_URL = "http://localhost:8000"

def log_section(title):
    print("\n" + "="*60)
    print(f" {title} ".center(60, "="))
    print("="*60 + "\n")

def run_demo():
    log_section("Demo 1: Happy Path (Auto Match & Completion)")
    print("Scenario: Invoice amount and PO match perfectly. No human intervention needed.")
    
    # Scenario 1: Happy Path
    payload_happy = {
        "invoice_id": "INV-HAPPY-001",
        "vendor_name": "Acme Corp",
        "vendor_tax_id": "TAX-123",
        "invoice_date": "2023-12-01",
        "due_date": "2024-01-01",
        "amount": 1000.0,
        "currency": "USD",
        "line_items": [
            {"desc": "AI Research Tools", "qty": 1, "unit_price": 1000.0, "total": 1000.0}
        ],
        "attachments": ["inv_1.pdf"],
        "mock_score": 0.95
    }
    
    resp = requests.post(f"{BASE_URL}/workflow/start", json=payload_happy)
    print(f"Workflow Status: {resp.json().get('status')}")
    
    # Show Final Structured Payload for Happy Path
    if resp.json().get('status') == "COMPLETE":
        print("\n[Output] Final Structured Payload (Happy Path):")
        # We need another call or a return to get the full state if the first call finished it
        print(json.dumps(resp.json(), indent=2))
    
    print("\nProcessing complete. Check server logs for Bigtool/MCP details.")
    
    time.sleep(1)
    
    log_section("Demo 2: HITL Path (Failed Match -> Human Decision)")
    print("Scenario: Match score is 0.75 (below 0.90 threshold). Workflow will pause.")
    
    # Scenario 2: HITL Path
    payload_hitl = {
        "invoice_id": "INV-FAIL-002",
        "vendor_name": "Globex Corp",
        "vendor_tax_id": "TAX-999",
        "invoice_date": "2023-12-05",
        "due_date": "2024-01-05",
        "amount": 5000.0,
        "currency": "USD",
        "line_items": [
            {"desc": "Consulting Services", "qty": 1, "unit_price": 5000.0, "total": 5000.0}
        ],
        "attachments": ["inv_2.pdf"],
        "mock_score": 0.75  # Forces HITL
    }
    
    print("\n[Input] Sample Invoice JSON (HITL Path):")
    print(json.dumps(payload_hitl, indent=2))
    
    resp = requests.post(f"{BASE_URL}/workflow/start", json=payload_hitl)
    data = resp.json()
    cp_id = data["checkpoint_id"]
    print(f"\nWorkflow State: {data.get('status')}")
    print(f"Review URL: {data.get('review_url')}")
    print(f"Checkpoint ID: {cp_id}")

    # Check pending review queue
    print("\n[Action] Fetching Human Review Queue...")
    pending = requests.get(f"{BASE_URL}/human-review/pending").json()
    print(f"Pending Items count: {len(pending['items'])}")
    
    # --- [INTERVIEW TIP] ---
    # I have commented out the code below so the workflow STAYS paused.
    # This allows you to open http://localhost:8000 and click 'ACCEPT' yourself!
    
    # log_section("Resuming Workflow: Human Decision = ACCEPT")
    # decision = {
    #     "checkpoint_id": cp_id,
    #     "decision": "ACCEPT",
    #     "notes": "Approved via manual script",
    #     "reviewer_id": "SANTOSH_CTO"
    # }
    # ...
    
    print("\n[Done] Workflow is currently PAUSED at CHECKPOINT_HITL.")
    print(">>> Stage-by-stage execution is visible in server logs.")
    print(f">>> Go to {BASE_URL} to review and ACCEPT the invoice manually! <<<")

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"Connection Error: {e}")
        print("Please ensure 'python app.py' is running in another terminal.")
