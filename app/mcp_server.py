import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from .db import get_db
from .models import Case, Party, TimelineEvent, FinancialRecord
from .rag_pipeline import LegalRAGEngine, LegalDocumentProcessor
from .schemas import CaseDetails, PartyOut, EventOut

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None

class MCPResponse(BaseModel):
    result: Any
    error: Optional[str] = None
    id: Optional[str] = None

class LegalMCPServer:
    def __init__(self):
        self.rag_engine = LegalRAGEngine()
        self.doc_processor = LegalDocumentProcessor()
        self.app = FastAPI(title="Legal AI MCP Server")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup MCP-compatible API routes"""
        
        @self.app.post("/mcp/query")
        async def mcp_query(request: MCPRequest, db: Session = Depends(get_db)):
            """Handle MCP-style queries with RAG integration"""
            try:
                if request.method == "legal.query":
                    return await self._handle_legal_query(request.params, db)
                elif request.method == "legal.analyze_document":
                    return await self._handle_document_analysis(request.params, db)
                elif request.method == "legal.generate_demand_letter":
                    return await self._handle_demand_letter_generation(request.params, db)
                elif request.method == "legal.get_case_context":
                    return await self._handle_case_context(request.params, db)
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown method: {request.method}")
            except Exception as e:
                logger.error(f"Error in MCP query: {e}")
                return MCPResponse(
                    result=None,
                    error=str(e),
                    id=request.id
                )
        
        @self.app.get("/mcp/tools")
        async def get_tools():
            """Return available MCP tools"""
            return {
                "tools": [
                    {
                        "name": "legal.query",
                        "description": "Query legal documents using RAG",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "Natural language query"},
                                "case_id": {"type": "string", "description": "Case identifier"},
                                "context": {"type": "object", "description": "Additional context"}
                            },
                            "required": ["query", "case_id"]
                        }
                    },
                    {
                        "name": "legal.analyze_document",
                        "description": "Analyze and process legal documents",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "Path to document"},
                                "case_id": {"type": "string", "description": "Case identifier"}
                            },
                            "required": ["file_path", "case_id"]
                        }
                    },
                    {
                        "name": "legal.generate_demand_letter",
                        "description": "Generate demand letter using RAG and case data",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "case_id": {"type": "string", "description": "Case identifier"},
                                "template_type": {"type": "string", "description": "Type of letter template"},
                                "additional_context": {"type": "object", "description": "Additional context"}
                            },
                            "required": ["case_id"]
                        }
                    },
                    {
                        "name": "legal.get_case_context",
                        "description": "Get comprehensive case context",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "case_id": {"type": "string", "description": "Case identifier"}
                            },
                            "required": ["case_id"]
                        }
                    }
                ]
            }
    
    async def _handle_legal_query(self, params: Dict[str, Any], db: Session) -> MCPResponse:
        """Handle legal queries using RAG"""
        query = params.get("query")
        case_id = params.get("case_id")
        context = params.get("context", {})
        
        if not query or not case_id:
            raise ValueError("Query and case_id are required")
        
        # Get case context from database
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        # Query RAG engine
        rag_response = await self.rag_engine.query(query, case_id, context)
        
        return MCPResponse(
            result={
                "answer": rag_response.answer,
                "sources": rag_response.sources,
                "context_used": rag_response.context_used,
                "case_id": case_id,
                "query": query
            }
        )
    
    async def _handle_document_analysis(self, params: Dict[str, Any], db: Session) -> MCPResponse:
        """Handle document analysis and processing"""
        file_path = params.get("file_path")
        case_id = params.get("case_id")
        
        if not file_path or not case_id:
            raise ValueError("file_path and case_id are required")
        
        # Process document using RAG pipeline
        doc_result = await self.doc_processor.process_document(file_path, case_id)
        
        return MCPResponse(
            result={
                "document_id": doc_result.id,
                "case_id": doc_result.case_id,
                "metadata": doc_result.metadata,
                "chunks_count": len(doc_result.chunks),
                "processing_status": "completed"
            }
        )
    
    async def _handle_demand_letter_generation(self, params: Dict[str, Any], db: Session) -> MCPResponse:
        """Generate demand letter using RAG and case data"""
        case_id = params.get("case_id")
        template_type = params.get("template_type", "demand_letter")
        additional_context = params.get("additional_context", {})
        
        if not case_id:
            raise ValueError("case_id is required")
        
        # Get case data
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        parties = db.query(Party).filter(Party.case_id == case_id).all()
        events = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()
        financials = db.query(FinancialRecord).filter(FinancialRecord.case_id == case_id).all()
        
        # Query RAG for relevant information
        rag_queries = [
            "Summarize medical expenses and treatment details",
            "Calculate lost wages and income impact",
            "Assess pain and suffering factors",
            "Identify liability and negligence evidence"
        ]
        
        rag_results = {}
        for query in rag_queries:
            response = await self.rag_engine.query(query, case_id, additional_context)
            rag_results[query] = response.answer
        
        # Generate letter content using RAG results
        letter_content = await self._generate_letter_content(
            case, parties, events, financials, rag_results, template_type
        )
        
        return MCPResponse(
            result={
                "letter_content": letter_content,
                "case_id": case_id,
                "template_type": template_type,
                "rag_context": rag_results,
                "generated_at": datetime.now().isoformat()
            }
        )
    
    async def _handle_case_context(self, params: Dict[str, Any], db: Session) -> MCPResponse:
        """Get comprehensive case context"""
        case_id = params.get("case_id")
        
        if not case_id:
            raise ValueError("case_id is required")
        
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        parties = db.query(Party).filter(Party.case_id == case_id).all()
        events = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()
        financials = db.query(FinancialRecord).filter(FinancialRecord.case_id == case_id).all()
        
        # Get RAG context
        rag_context = await self.rag_engine.query(
            "Provide comprehensive case summary and key facts", 
            case_id, 
            {}
        )
        
        return MCPResponse(
            result={
                "case": {
                    "case_id": case.case_id,
                    "case_type": case.case_type,
                    "date_filed": case.date_filed.isoformat() if case.date_filed else None,
                    "status": case.status,
                    "case_summary": case.case_summary
                },
                "parties": [
                    {
                        "party_id": p.party_id,
                        "party_type": p.party_type,
                        "name": p.name,
                        "contact_info": p.contact_info
                    } for p in parties
                ],
                "events": [
                    {
                        "event_id": e.event_id,
                        "event_date": e.event_date.isoformat() if e.event_date else None,
                        "description": e.description
                    } for e in events
                ],
                "financials": [
                    {
                        "record_id": f.record_id,
                        "record_type": f.record_type,
                        "amount": f.amount,
                        "description": f.description
                    } for f in financials
                ],
                "rag_summary": rag_context.answer,
                "rag_sources": rag_context.sources
            }
        )
    
    async def _generate_letter_content(
        self, 
        case: Case, 
        parties: List[Party], 
        events: List[TimelineEvent], 
        financials: List[FinancialRecord],
        rag_results: Dict[str, str],
        template_type: str
    ) -> str:
        """Generate letter content using RAG results and case data"""
        
        # Extract key information from RAG results
        medical_info = rag_results.get("Summarize medical expenses and treatment details", "")
        lost_wages_info = rag_results.get("Calculate lost wages and income impact", "")
        pain_suffering_info = rag_results.get("Assess pain and suffering factors", "")
        liability_info = rag_results.get("Identify liability and negligence evidence", "")
        
        # Calculate totals from financial records
        medical_total = sum(f.amount for f in financials if f.record_type == "medical")
        lost_wages_total = sum(f.amount for f in financials if f.record_type == "lost_wages")
        pain_suffering_total = sum(f.amount for f in financials if f.record_type == "pain_suffering")
        
        # Find defendant (assuming first party that's not the client)
        defendant = next((p for p in parties if p.party_type == "defendant"), None)
        client = next((p for p in parties if p.party_type == "plaintiff"), None)
        
        # Generate letter content
        letter_content = f"""
[LAW FIRM LETTERHEAD]
{datetime.now().strftime('%B %d, %Y')}

{defendant.name if defendant else 'Defendant'}
Attn: Claims Department

Re: Demand for ${medical_total + lost_wages_total + pain_suffering_total:,} – Case {case.case_id}

Dear Sir or Madam:

On behalf of our client, {client.name if client else 'our client'}, we demand payment of ${medical_total + lost_wages_total + pain_suffering_total:,} for injuries sustained due to your insured's negligence.

BASED ON OUR ANALYSIS OF THE CASE DOCUMENTS:

{medical_info}

{lost_wages_info}

{pain_suffering_info}

LIABILITY EVIDENCE:
{liability_info}

DETAILED BREAKDOWN:
1. Medical Expenses: ${medical_total:,}
2. Lost Wages: ${lost_wages_total:,}
3. Pain & Suffering: ${pain_suffering_total:,}
TOTAL DEMAND: ${medical_total + lost_wages_total + pain_suffering_total:,}

Please remit payment within 30 days of this letter.

Sincerely,

[Attorney Name]
        """
        
        return letter_content.strip()

# Create MCP server instance
mcp_server = LegalMCPServer()
app = mcp_server.app 