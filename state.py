from typing import TypedDict, List, Optional, Any, Dict

class InvoiceState(TypedDict):
    # INTAKE
    invoice_payload: Dict[str, Any]
    raw_id: Optional[str]
    ingest_ts: Optional[str]
    validated: bool
    
    # UNDERSTAND
    parsed_invoice: Optional[Dict[str, Any]]
    
    # PREPARE
    vendor_profile: Optional[Dict[str, Any]]
    normalized_invoice: Optional[Dict[str, Any]]
    flags: Optional[Dict[str, Any]]
    
    # RETRIEVE
    matched_pos: Optional[List[Dict[str, Any]]]
    matched_grns: Optional[List[Dict[str, Any]]]
    history: Optional[List[Dict[str, Any]]]
    
    # MATCH
    match_score: float
    match_result: Optional[str]
    tolerance_pct: float
    match_evidence: Optional[Dict[str, Any]]
    
    # HITL
    # HITL
    hitl_checkpoint_id: Optional[str]

    review_url: Optional[str]
    paused_reason: Optional[str]
    human_decision: Optional[str]  # 'ACCEPT' or 'REJECT'
    reviewer_id: Optional[str]
    human_notes: Optional[str]
    created_at: Optional[str]
    resume_token: Optional[str]
    next_stage_override: Optional[str]
    
    # RECONCILE
    accounting_entries: Optional[List[Dict[str, Any]]]
    reconciliation_report: Optional[Dict[str, Any]]
    
    # APPROVE
    approval_status: Optional[str]
    approver_id: Optional[str]
    
    # POSTING
    posted: bool
    erp_txn_id: Optional[str]
    scheduled_payment_id: Optional[str]
    
    # NOTIFY
    notify_status: Optional[Dict[str, Any]]
    notified_parties: Optional[List[str]]
    
    # COMPLETE
    final_payload: Optional[Dict[str, Any]]
    audit_log: List[str]
    workflow_status: str  # 'IN_PROGRESS', 'PAUSED', 'COMPLETED', 'FAILED', 'MANUAL_HANDOFF'
