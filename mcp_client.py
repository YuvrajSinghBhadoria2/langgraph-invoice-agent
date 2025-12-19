from typing import Any, Dict

class MCPClient:
    """
    MCP Client to route calls to COMMON or ATLAS servers.
    """
    @staticmethod
    def execute_ability(server: str, ability: str, params: Dict[str, Any]) -> Any:
        print(f"[MCP] Routing ability '{ability}' to '{server}' server with params: {params}")
        
        # Simulated responses based on business logic requirements
        if server == "COMMON":
            if ability == "accept_invoice_payload":
                return {"raw_id": "INV-12345", "ingest_ts": "2023-10-27T10:00:00Z", "validated": True}
            elif ability == "parsing":
                return {
                    "invoice_text": "Extracted text...",
                    "parsed_line_items": [{"desc": "Laptop", "qty": 1, "unit_price": 1200, "total": 1200}],
                    "detected_pos": ["PO-999"],
                    "currency": "USD",
                    "parsed_dates": {"invoice_date": "2023-10-26", "due_date": "2023-11-26"}
                }
            elif ability == "normalize_vendor":
                return {"normalized_name": "Tech Corp", "tax_id": "TX-789"}
            elif ability == "compute_flags":
                return {"missing_info": [], "risk_score": 0.1}
            elif ability == "compute_match_score":
                # Deterministic for demo purposes, can be controlled via params
                score = params.get("mock_score", 0.95)
                return {
                    "match_score": score,
                    "match_result": "MATCHED" if score >= 0.9 else "FAILED",
                    "tolerance_pct": 2.0,
                    "match_evidence": {"po_matched": True, "amount_matched": True}
                }
            elif ability == "save_state_for_human_review":
                return {
                    "checkpoint_id": "CHK-456",
                    "review_url": f"http://localhost:8000/review/CHK-456",
                    "paused_reason": "Match score below threshold"
                }
            elif ability == "build_accounting_entries":
                return [
                    {"account": "Accounts Payable", "type": "CREDIT", "amount": 1200},
                    {"account": "Inventory", "type": "DEBIT", "amount": 1200}
                ]
            elif ability == "output_final_payload":
                return {"status": "SUCCESS", "message": "Workflow completed"}

        elif server == "ATLAS":
            if ability == "ocr_extract":
                return {"ocr_status": "Success", "page_count": 1}
            elif ability == "enrich_vendor":
                return {"enrichment_meta": {"credit_score": "AAA", "industry": "Technology"}}
            elif ability == "fetch_po":
                return [{"po_id": "PO-999", "expected_amount": 1200}]
            elif ability == "fetch_grn":
                return [{"grn_id": "GRN-777", "po_id": "PO-999"}]
            elif ability == "fetch_history":
                return []
            elif ability == "accept_or_reject_invoice":
                return {"human_decision": params.get("decision", "ACCEPT"), "reviewer_id": "REV-001"}
            elif ability == "apply_invoice_approval_policy":
                return {"approval_status": "AUTO_APPROVED", "approver_id": "SYSTEM"}
            elif ability == "post_to_erp":
                return {"posted": True, "erp_txn_id": "ERP-XYZ"}
            elif ability == "schedule_payment":
                return {"scheduled_payment_id": "PAY-888"}
            elif ability == "notify_vendor":
                return {"email_sent": True}
            elif ability == "notify_finance_team":
                return {"slack_notified": True}

        return {"error": "Ability not found"}
