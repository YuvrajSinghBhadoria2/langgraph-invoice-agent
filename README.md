# LangGraph Invoice Processing Agent (Langie)

This project implements a comprehensive Invoice Processing workflow using **LangGraph**, featuring Human-In-The-Loop (HITL) checkpoints, MCP client orchestration, and dynamic tool selection via **Bigtool**.

## Project Overview
The agent, named **Langie**, processes invoices through 12 distinct stages, managing complex state and external system interactions. It is designed to be resilient, autonomous, and human-guided.

### Key Features
- **Dynamic Graph Construction**: Unlike basic implementations, this agent **dynamically builds its architecture** at runtime by reading `workflow.json`. This makes the system extremely flexible and configuration-driven.
- **12-Stage Workflow**: Implements the full lifecycle from `INTAKE` to `COMPLETE`.
- **Visual Graph API**: Visit `/workflow/visualize` to see a real-time Mermaid diagram of the agent's logic.
- **Human-In-The-Loop (HITL)**: Automatically interrupts execution for human review when matching scores fall below the 90% threshold.
- **Premium Review Dashboard**: A custom-built, modern UI at the root URL (`/`) for managing pending reviews.
- **MCP Client Orchestration**: Routes abilities to specialized `COMMON` and `ATLAS` servers as per stage requirements.
- **Bigtool Selection**: Dynamically chooses the best tool from pools for OCR, Enrichment, ERP, and Database interactions.
- **State Persistence**: Uses LangGraph's `SqliteSaver` for reliable pause/resume and state durability across restarts.

## Technical Stack
- **Framework**: LangGraph / LangChain
- **API Engine**: FastAPI
- **Process Manager**: Uvicorn
- **Language**: Python 3.10+

## Project Structure
- `workflow.json`: The LangGraph Agent Config defining stages and tools.
- `state.py`: TypedDict schema for persistent workflow state.
- `nodes.py`: Implementation of the 12 workflow stages as LangGraph nodes.
- `graph.py`: Assembly of the state graph, edges, and HITL interrupts.
- `app.py`: FastAPI application for starting and managing workflows.
- `mcp_client.py`: Routing logic for MCP abilities.
- `bigtool.py`: Dynamic tool selection logic.
- `demo_client.py`: Comprehensive demo script to showcase end-to-end execution.

## Getting Started

### 1. Install Dependencies
```bash
pip install langgraph fastapi uvicorn pydantic python-dotenv requests
```

### 2. Run the API Server
```bash
export PYTHONPATH=$PYTHONPATH:.
python app.py
```
The server will start at `http://localhost:8000`. You can view the interactive documentation at `http://localhost:8000/docs`.

### 3. Run the Demo
While the server is running, execute the demo script in a new terminal:
```bash
python demo_client.py
```
This script will demonstrate:
1. **Happy Path**: An invoice that auto-approves.
2. **HITL Path**: An invoice that pauses for manual review, is accepted via the API, and then completes.


