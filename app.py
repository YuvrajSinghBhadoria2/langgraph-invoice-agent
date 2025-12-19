from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from graph import build_graph
from datetime import datetime
import uuid
import os
import json

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Invoice Processing HITL API")

# Mount static files to serve assets
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    # Return the premium dashboard as the homepage
    return FileResponse("static/index.html")

invoice_graph = build_graph()

# In-memory storage for active threads for demo purposes
active_threads = {}

class LineItem(BaseModel):
    desc: str
    qty: float
    unit_price: float
    total: float

class InvoicePayload(BaseModel):
    invoice_id: str
    vendor_name: str
    vendor_tax_id: str
    invoice_date: str
    due_date: str
    amount: float
    currency: str
    line_items: List[LineItem]
    attachments: List[str]
    mock_score: Optional[float] = 0.95

class DecisionPayload(BaseModel):
    checkpoint_id: str  # maps to our thread_id
    decision: str       # 'ACCEPT' or 'REJECT'
    notes: Optional[str] = None
    reviewer_id: str

@app.get("/workflow/config")
async def get_workflow_config():
    # Serve the workflow stages to the UI for rendering the progress tracker
    config_path = os.path.join(os.path.dirname(__file__), "workflow.json")
    with open(config_path, "r") as f:
        data = json.load(f)
    return {"stages": [s["id"] for s in data["stages"]]}

@app.post("/workflow/start")
async def start_workflow(payload: InvoicePayload):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    active_threads[thread_id] = config
    
    # Initial state
    initial_state = {
        "invoice_payload": payload.model_dump(),
        "workflow_status": "START",
        "audit_log": [f"Workflow started for {payload.invoice_id}"],
        "created_at": datetime.now().isoformat()
    }
    
    try:
        final_state = invoice_graph.invoke(initial_state, config=config)
        
        # Check if the graph is paused at HITL_DECISION
        state = invoice_graph.get_state(config)
        is_paused = len(state.next) > 0 and state.next[0] == "HITL_DECISION"
        
        return {
            "checkpoint_id": thread_id,
            "status": "PAUSED" if is_paused else final_state.get("workflow_status"),
            "review_url": f"http://localhost:8000/review/{thread_id}" if is_paused else None,
            "final_payload": final_state.get("final_payload") if not is_paused else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/human-review/pending")
async def get_pending_reviews():
    # Strict alignment with Appendix-1: checkpoint_id, invoice_id, vendor_name, amount, created_at, reason_for_hold, review_url
    pending = []
    for thread_id, config in active_threads.items():
        state = invoice_graph.get_state(config)
        if state.next and state.next[0] == "HITL_DECISION":
            snapshot = state.values
            if snapshot:
                pending.append({
                    "checkpoint_id": thread_id,
                    "invoice_id": snapshot["invoice_payload"]["invoice_id"],
                    "vendor_name": snapshot["vendor_profile"]["normalized_name"],
                    "amount": snapshot["invoice_payload"]["amount"],
                    "created_at": snapshot.get("created_at"),
                    "reason_for_hold": snapshot["paused_reason"],
                    "review_url": f"http://localhost:8000/review/{thread_id}"
                })
    return {"items": pending}

@app.get("/workflow/logs")
async def get_workflow_logs():
    # Return the logs of all active and completed threads for the dashboard
    logs = []
    for thread_id, config in active_threads.items():
        state = invoice_graph.get_state(config)
        snapshot = state.values
        if snapshot:
            logs.append({
                "thread_id": thread_id,
                "invoice_id": snapshot["invoice_payload"]["invoice_id"],
                "status": snapshot.get("workflow_status"),
                "audit": snapshot.get("audit_log", [])
            })
    return {"logs": logs}

@app.get("/workflow/visualize")
async def visualize_workflow():
    # Generate Mermaid diagram using LangGraph's native graph object
    mermaid_graph = invoice_graph.get_graph().draw_mermaid()
    # Use Mermaid.ink to provide a visual representation in the browser
    import base64
    encoded = base64.b64encode(mermaid_graph.encode('ascii')).decode('ascii')
    image_url = f"https://mermaid.ink/img/{encoded}"
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=f'<html><body style="background:#0a0e17;display:flex;justify-content:center;padding:50px;"><img src="{image_url}" style="max-width:100%;box-shadow:0 0 50px rgba(79,70,229,0.2);border-radius:10px;"/></body></html>')

@app.post("/human-review/decision")
async def submit_decision(payload: DecisionPayload):
    # Strict alignment with Appendix-1: request includes checkpoint_id, decision, notes, reviewer_id
    thread_id = payload.checkpoint_id
    
    if thread_id not in active_threads:
        config = {"configurable": {"thread_id": thread_id}}
        active_threads[thread_id] = config
    
    config = active_threads[thread_id]
    
    # Update state with decision
    invoice_graph.update_state(config, {
        "human_decision": payload.decision,
        "reviewer_id": payload.reviewer_id,
        "human_notes": payload.notes
    })
    
    # Resume workflow
    final_state = invoice_graph.invoke(None, config=config)
    
    # Response schema: resume_token, next_stage
    return {
        "resume_token": f"token-{thread_id}",
        "next_stage": "RECONCILE" if payload.decision == "ACCEPT" else "END"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

