from datetime import datetime
from state import InvoiceState
from bigtool import BigtoolPicker
from mcp_client import MCPClient

def intake_node(state: InvoiceState):
    print("--- INTAKE ---")
    storage_tool = BigtoolPicker.select("storage", ["s3", "gcs", "local_fs"])
    result = MCPClient.execute_ability("COMMON", "accept_invoice_payload", state["invoice_payload"])
    return {
        "raw_id": result["raw_id"],
        "ingest_ts": result["ingest_ts"],
        "validated": result["validated"],
        "workflow_status": "IN_PROGRESS",
        "audit_log": state.get("audit_log", []) + [f"Langie: Ingested payload and persisted raw data using {storage_tool}."]
    }

def understand_node(state: InvoiceState):
    print("--- UNDERSTAND ---")
    ocr_tool = BigtoolPicker.select("ocr", ["google_vision", "tesseract", "aws_textract"])
    MCPClient.execute_ability("ATLAS", "ocr_extract", {"tool": ocr_tool})
    result = MCPClient.execute_ability("COMMON", "parsing", {})
    return {
        "parsed_invoice": result,
        "audit_log": state["audit_log"] + [f"Langie: Extracted text via {ocr_tool} and successfully parsed line items."]
    }

def prepare_node(state: InvoiceState):
    print("--- PREPARE ---")
    enrich_tool = BigtoolPicker.select("enrichment", ["clearbit", "people_data_labs", "vendor_db"])
    vendor = MCPClient.execute_ability("COMMON", "normalize_vendor", {})
    meta = MCPClient.execute_ability("ATLAS", "enrich_vendor", {"tool": enrich_tool})
    flags = MCPClient.execute_ability("COMMON", "compute_flags", {})
    
    vendor["enrichment_meta"] = meta["enrichment_meta"]
    
    return {
        "vendor_profile": vendor,
        "flags": flags,
        "audit_log": state["audit_log"] + [f"Langie: Normalized vendor and enriched profile using {enrich_tool}."]
    }

def retrieve_node(state: InvoiceState):
    print("--- RETRIEVE ---")
    erp_tool = BigtoolPicker.select("erp_connector", ["sap_sandbox", "netsuite", "mock_erp"])
    pos = MCPClient.execute_ability("ATLAS", "fetch_po", {"tool": erp_tool})
    grns = MCPClient.execute_ability("ATLAS", "fetch_grn", {"tool": erp_tool})
    history = MCPClient.execute_ability("ATLAS", "fetch_history", {"tool": erp_tool})
    
    return {
        "matched_pos": pos,
        "matched_grns": grns,
        "history": history,
        "audit_log": state["audit_log"] + [f"Langie: Successfully retrieved PO/GRN documents from {erp_tool}."]
    }

def match_node(state: InvoiceState):
    print("--- MATCH_TWO_WAY ---")
    # For simulation, we can pass a mock score if provided in payload
    mock_score = state["invoice_payload"].get("mock_score", 0.95)
    result = MCPClient.execute_ability("COMMON", "compute_match_score", {"mock_score": mock_score})
    
    return {
        "match_score": result["match_score"],
        "match_result": result["match_result"],
        "tolerance_pct": result["tolerance_pct"],
        "match_evidence": result["match_evidence"],
        "audit_log": state["audit_log"] + [f"Langie: Computed 2-way match score of {result['match_score']}."]
    }

def checkpoint_node(state: InvoiceState):
    print("--- CHECKPOINT_HITL ---")
    if state["match_result"] != "FAILED":
        return {} # Should not be reached if routing is correct
        
    db_tool = BigtoolPicker.select("db", ["postgres", "sqlite", "dynamodb"])
    result = MCPClient.execute_ability("COMMON", "save_state_for_human_review", {"db": db_tool})
    
    return {
        "checkpoint_id": result["checkpoint_id"],
        "review_url": result["review_url"],
        "paused_reason": result["paused_reason"],
        "workflow_status": "PAUSED",
        "audit_log": state["audit_log"] + [f"Langie: Triggered HITL checkpoint due to low match score (Stored in {db_tool})."]
    }

def hitl_decision_node(state: InvoiceState):
    print("--- HITL_DECISION ---")
    # Record decision via ATLAS server as per requirement
    MCPClient.execute_ability("ATLAS", "accept_or_reject_invoice", {
        "decision": state.get("human_decision"),
        "reviewer_id": state.get("reviewer_id")
    })
    
    if state.get("human_decision") == "REJECT":
        return {
            "workflow_status": "MANUAL_HANDOFF",
        "audit_log": state["audit_log"] + ["Langie: Human REJECTED invoice. Finalizing with MANUAL_HANDOFF status."]
        }
    
    return {
        "workflow_status": "IN_PROGRESS",
        "audit_log": state["audit_log"] + [f"Langie: Human ACCEPTED invoice (Reviewer: {state.get('reviewer_id')}). Resuming workflow."]
    }

def reconcile_node(state: InvoiceState):
    print("--- RECONCILE ---")
    entries = MCPClient.execute_ability("COMMON", "build_accounting_entries", {})
    return {
        "accounting_entries": entries,
        "audit_log": state["audit_log"] + ["Langie: Reconstructed accounting entries and ledger records."]
    }

def approve_node(state: InvoiceState):
    print("--- APPROVE ---")
    result = MCPClient.execute_ability("ATLAS", "apply_invoice_approval_policy", {})
    return {
        "approval_status": result["approval_status"],
        "approver_id": result["approver_id"],
        "audit_log": state["audit_log"] + ["Langie: Applied approval policies and verified thresholds."]
    }

def posting_node(state: InvoiceState):
    print("--- POSTING ---")
    erp_tool = BigtoolPicker.select("erp_connector", ["sap_sandbox", "netsuite", "mock_erp"])
    post = MCPClient.execute_ability("ATLAS", "post_to_erp", {"tool": erp_tool})
    pay = MCPClient.execute_ability("ATLAS", "schedule_payment", {})
    
    return {
        "posted": post["posted"],
        "erp_txn_id": post["erp_txn_id"],
        "scheduled_payment_id": pay["scheduled_payment_id"],
        "audit_log": state["audit_log"] + [f"Langie: Posted to ERP system ({erp_tool}) and scheduled payment."]
    }

def notify_node(state: InvoiceState):
    print("--- NOTIFY ---")
    email_tool = BigtoolPicker.select("email", ["sendgrid", "smartlead", "ses"])
    MCPClient.execute_ability("ATLAS", "notify_vendor", {"tool": email_tool})
    MCPClient.execute_ability("ATLAS", "notify_finance_team", {})
    
    return {
        "notify_status": {"success": True},
        "notified_parties": ["vendor", "finance_team"],
        "audit_log": state["audit_log"] + [f"Langie: Notifications dispatched to vendor and finance via {email_tool}."]
    }

def complete_node(state: InvoiceState):
    print("--- COMPLETE ---")
    db_tool = BigtoolPicker.select("db", ["postgres", "sqlite", "dynamodb"])
    result = MCPClient.execute_ability("COMMON", "output_final_payload", {"db": db_tool})
    
    final_payload = {
        "invoice_id": state["raw_id"],
        "vendor": state["vendor_profile"]["normalized_name"],
        "amount": state["invoice_payload"]["amount"],
        "status": "COMPLETE",
        "audit": state["audit_log"]
    }
    
    return {
        "final_payload": final_payload,
        "workflow_status": "COMPLETE",
        "audit_log": state["audit_log"] + ["Langie: Workflow complete. Final structured payload generated."]
    }
