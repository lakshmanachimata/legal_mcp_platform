from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Body, Form, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black
from . import models, db
from .rag_pipeline import LegalDocumentProcessor, LegalRAGEngine
from .config import LLMProvider, LLMConfig, config
from .llm_factory import LLMFactory

models.Base.metadata.create_all(bind=db.engine)

app = FastAPI(
    title="Legal AI Case Management System",
    description="""
    ## Legal AI Case Management System API
    
    A comprehensive legal case management system with AI-powered document processing, RAG (Retrieval-Augmented Generation), and demand letter generation capabilities.
    
    ### Key Features:
    - **Document Processing**: Upload and analyze legal documents with AI
    - **RAG Queries**: Intelligent document retrieval and question answering
    - **Demand Letter Generation**: AI-powered legal document creation
    - **Case Management**: Complete case tracking and management
    - **PDF Generation**: Professional document output
    
    ### LLM Providers:
    - **OpenAI**: Cloud-based AI models (GPT-4, GPT-3.5)
    - **Ollama**: Local AI models (Mistral, Llama, etc.)
    
    ### Environment Configuration:
    The system uses environment variables for configuration:
    - `LLM_PROVIDER`: ollama or openai
    - `LLM_MODEL`: Model name (e.g., gpt-4o-mini, mistral)
    - `OPENAI_API_KEY`: API key for OpenAI
    - `OLLAMA_BASE_URL`: URL for Ollama server
    """,
    version="1.0.0",
    contact={
        "name": "Legal AI Development Team",
        "email": "support@legal-ai.com",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG components
rag_engine = LegalRAGEngine()
doc_processor = LegalDocumentProcessor()

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()

# Basic CRUD endpoints
@app.get("/cases", tags=["Case Management"], summary="Get all cases", description="Retrieve all cases from the database")
def get_cases(db: Session = Depends(get_db)):
    """Get all cases in the system"""
    return db.query(models.Case).all()

@app.get("/parties", tags=["Case Management"], summary="Get all parties", description="Retrieve all parties from the database")
def get_parties(db: Session = Depends(get_db)):
    """Get all parties in the system"""
    return db.query(models.Party).all()

@app.get("/events", tags=["Case Management"], summary="Get all events", description="Retrieve all timeline events from the database")
def get_events(db: Session = Depends(get_db)):
    """Get all timeline events in the system"""
    return db.query(models.TimelineEvent).all()

@app.get("/financials", tags=["Case Management"], summary="Get all financials", description="Retrieve all financial records from the database")
def get_financials(db: Session = Depends(get_db)):
    """Get all financial records in the system"""
    return db.query(models.FinancialRecord).all()

@app.get("/system/overview", tags=["System"], summary="Get system overview", description="Get comprehensive system overview with all cases, statistics, and details")
async def get_system_overview():
    """Get comprehensive system overview with all cases, statistics, and details"""
    try:
        response = await rag_engine.query("overall cases details", "system", {})
        return {
            "overview": response.answer,
            "statistics": {
                "total_cases": response.sources[0].get('total_cases', 0),
                "total_amount": response.sources[0].get('total_amount', 0),
                "query_type": "system_overview"
            },
            "context_used": response.context_used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/statistics", tags=["System"], summary="Get system statistics", description="Get system statistics and case counts")
async def get_system_statistics():
    """Get system statistics and case counts"""
    try:
        response = await rag_engine.query("total number of cases", "system", {})
        return {
            "statistics": response.answer,
            "context_used": response.context_used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/timeline", tags=["System"], summary="Get system timeline", description="Get comprehensive timeline of all cases with dates")
async def get_system_timeline():
    """Get comprehensive timeline of all cases with dates"""
    try:
        response = await rag_engine.query("show me all cases with their dates", "system", {})
        return {
            "timeline": response.answer,
            "context_used": response.context_used
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cases/{case_id}/comprehensive")
async def get_case_comprehensive(case_id: str):
    """Get comprehensive information for a specific case including timeline, parties, financials"""
    try:
        # Get case data
        db_session = db.SessionLocal()
        try:
            case = db_session.query(models.Case).filter(models.Case.case_id == case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
            
            parties = db_session.query(models.Party).filter(models.Party.case_id == case_id).all()
            events = db_session.query(models.TimelineEvent).filter(models.TimelineEvent.case_id == case_id).all()
            financials = db_session.query(models.FinancialRecord).filter(models.FinancialRecord.case_id == case_id).all()
            
            # Calculate financial totals
            total_amount = sum(f.amount for f in financials) if financials else 0
            
            # Format timeline events
            timeline_events = []
            for event in events:
                timeline_events.append({
                    'date': event.event_date.strftime('%Y-%m-%d') if event.event_date else 'Unknown',
                    'description': event.description
                })
            
            return {
                "case": {
                    "case_id": case.case_id,
                    "case_type": case.case_type,
                    "status": case.status,
                    "date_filed": case.date_filed.strftime('%Y-%m-%d') if case.date_filed else 'Unknown',
                    "summary": case.case_summary
                },
                "parties": [{"type": p.party_type, "name": p.name, "contact": p.contact_info} for p in parties],
                "timeline_events": timeline_events,
                "financials": {
                    "total_amount": total_amount,
                    "records": [{"type": f.record_type, "amount": f.amount, "description": f.description} for f in financials]
                },
                "statistics": {
                    "parties_count": len(parties),
                    "events_count": len(events),
                    "financials_count": len(financials)
                }
            }
        finally:
            db_session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/all", tags=["System"], summary="Get all system information", description="Get comprehensive system information including cases, parties, events, and financials")
async def get_all_system_information():
    """Get all system information including overview, statistics, timeline, and all cases"""
    try:
        # Get system overview
        overview_response = await rag_engine.query("overall cases details", "system", {})
        
        # Get system statistics
        stats_response = await rag_engine.query("total number of cases", "system", {})
        
        # Get system timeline
        timeline_response = await rag_engine.query("show me all cases with their dates", "system", {})
        
        # Get all cases with comprehensive data
        db_session = db.SessionLocal()
        try:
            cases = db_session.query(models.Case).all()
            all_cases_data = []
            
            for case in cases:
                parties = db_session.query(models.Party).filter(models.Party.case_id == case.case_id).all()
                events = db_session.query(models.TimelineEvent).filter(models.TimelineEvent.case_id == case.case_id).all()
                financials = db_session.query(models.FinancialRecord).filter(models.FinancialRecord.case_id == case.case_id).all()
                
                total_amount = sum(f.amount for f in financials) if financials else 0
                
                timeline_events = []
                for event in events:
                    timeline_events.append({
                        'date': event.event_date.strftime('%Y-%m-%d') if event.event_date else 'Unknown',
                        'description': event.description
                    })
                
                all_cases_data.append({
                    "case": {
                        "case_id": case.case_id,
                        "case_type": case.case_type,
                        "status": case.status,
                        "date_filed": case.date_filed.strftime('%Y-%m-%d') if case.date_filed else 'Unknown',
                        "summary": case.case_summary
                    },
                    "parties": [{"type": p.party_type, "name": p.name, "contact": p.contact_info} for p in parties],
                    "timeline_events": timeline_events,
                    "financials": {
                        "total_amount": total_amount,
                        "records": [{"type": f.record_type, "amount": f.amount, "description": f.description} for f in financials]
                    },
                    "statistics": {
                        "parties_count": len(parties),
                        "events_count": len(events),
                        "financials_count": len(financials)
                    }
                })
        finally:
            db_session.close()
        
        return {
            "system_overview": overview_response.answer,
            "system_statistics": stats_response.answer,
            "system_timeline": timeline_response.answer,
            "all_cases": all_cases_data,
            "summary": {
                "total_cases": len(cases),
                "total_financial_amount": sum(case['financials']['total_amount'] for case in all_cases_data),
                "total_events": sum(case['statistics']['events_count'] for case in all_cases_data),
                "total_parties": sum(case['statistics']['parties_count'] for case in all_cases_data)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# RAG and MCP Integration Endpoints
@app.post("/rag/query", tags=["RAG"], summary="Query RAG system", description="Query the RAG system with natural language questions about cases and documents")
async def rag_query(
    query: str = Body(..., description="Natural language query about the case or documents"),
    case_id: str = Body(default=None, description="Case ID to query (optional)"),
    context: Dict[str, Any] = Body(default={}, description="Additional context for the query")
):
    """Query legal documents using RAG - supports both case-specific and system-wide queries"""
    try:
        # For system-wide queries, use a default case_id if none provided
        if not case_id:
            case_id = "system"
        
        response = await rag_engine.query(query, case_id, context)
        return {
            "answer": response.answer,
            "sources": response.sources,
            "context_used": response.context_used,
            "case_id": case_id,
            "query": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query-with-provider", tags=["RAG"], summary="Query RAG with custom LLM provider", description="Query the RAG system with a custom LLM provider configuration")
async def rag_query_with_provider(
    query: str = Form(..., description="Natural language query about the case or documents"),
    case_id: str = Form(default=None, description="Case ID to query (optional)"),
    provider: str = Form(default="ollama", description="LLM provider: ollama or openai"),
    model: str = Form(default="mistral", description="Model name for the LLM provider"),
    base_url: Optional[str] = Form(default=None, description="Base URL for Ollama (optional)"),
    api_key: Optional[str] = Form(default=None, description="API key for OpenAI (optional)"),
    temperature: float = Form(default=0.0, description="Temperature for LLM generation"),
    context: Dict[str, Any] = Body(default={}, description="Additional context for the query")
):
    """Query legal documents using RAG with configurable LLM provider"""
    try:
        # For system-wide queries, use a default case_id if none provided
        if not case_id:
            case_id = "system"
        
        # Create LLM configuration from form arguments
        llm_config = LLMConfig(
            provider=LLMProvider(provider),
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature
        )
        
        # Create RAG engine with custom LLM configuration
        custom_rag_engine = LegalRAGEngine(llm_config)
        
        response = await custom_rag_engine.query(query, case_id, context)
        return {
            "answer": response.answer,
            "sources": response.sources,
            "context_used": response.context_used,
            "case_id": case_id,
            "query": query,
            "llm_provider": provider,
            "llm_model": model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/process_document", tags=["Document Processing"], summary="Process document", description="Process and analyze legal documents using the default LLM configuration")
async def process_document(
    file: UploadFile = File(..., description="PDF document to process"),
    case_id: str = Form(..., description="Case ID to associate the document with")
):
    """Process and analyze legal documents"""
    try:
        if not case_id:
            raise HTTPException(status_code=400, detail="case_id is required")
        
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        doc_result = await doc_processor.process_document(temp_path, case_id)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "document_id": doc_result.id,
            "case_id": doc_result.case_id,
            "metadata": doc_result.metadata,
            "chunks_count": len(doc_result.chunks),
            "processing_status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/process_document-with-provider", tags=["Document Processing"], summary="Process document with custom LLM", description="Process and analyze legal documents with configurable LLM provider")
async def process_document_with_provider(
    file: UploadFile = File(..., description="PDF document to process"),
    case_id: str = Form(..., description="Case ID to associate the document with"),
    provider: str = Form(default="ollama", description="LLM provider: ollama or openai"),
    model: str = Form(default="mistral", description="Model name for the LLM provider"),
    base_url: Optional[str] = Form(default=None, description="Base URL for Ollama (optional)"),
    api_key: Optional[str] = Form(default=None, description="API key for OpenAI (optional)"),
    temperature: float = Form(default=0.0, description="Temperature for LLM generation")
):
    """Process and analyze legal documents with configurable LLM provider"""
    try:
        if not case_id:
            raise HTTPException(status_code=400, detail="case_id is required")
        
        # Create LLM configuration from form arguments
        llm_config = LLMConfig(
            provider=LLMProvider(provider),
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature
        )
        
        # Create document processor with custom LLM configuration
        custom_doc_processor = LegalDocumentProcessor(llm_config)
        
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        doc_result = await custom_doc_processor.process_document(temp_path, case_id)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "document_id": doc_result.id,
            "case_id": doc_result.case_id,
            "metadata": doc_result.metadata,
            "chunks_count": len(doc_result.chunks),
            "processing_status": "completed",
            "llm_provider": provider,
            "llm_model": model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/process_folder", tags=["Document Processing"], summary="Process all documents in a folder", description="Process and analyze all PDF documents in a specified folder for a case")
async def process_folder(
    folder_path: str = Form(..., description="Path to folder containing PDF documents"),
    case_id: str = Form(..., description="Case ID to associate the documents with"),
    provider: str = Form(default="ollama", description="LLM provider: ollama or openai"),
    model: str = Form(default="mistral", description="Model name for the LLM provider"),
    base_url: Optional[str] = Form(default=None, description="Base URL for Ollama (optional)"),
    api_key: Optional[str] = Form(default=None, description="API key for OpenAI (optional)"),
    temperature: float = Form(default=0.0, description="Temperature for LLM generation")
):
    """Process all PDF documents in a folder for a case"""
    try:
        if not case_id:
            raise HTTPException(status_code=400, detail="case_id is required")
        
        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path is required")
        
        # Validate folder path
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=400, detail=f"Folder path does not exist: {folder_path}")
        
        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
        
        # Create LLM configuration from form arguments
        llm_config = LLMConfig(
            provider=LLMProvider(provider),
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature
        )
        
        # Create document processor with custom LLM configuration
        custom_doc_processor = LegalDocumentProcessor(llm_config)
        
        # Find all PDF files in the folder
        pdf_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(folder_path, file))
        
        if not pdf_files:
            raise HTTPException(status_code=400, detail=f"No PDF files found in folder: {folder_path}")
        
        # Process all documents
        results = []
        errors = []
        
        for pdf_file in pdf_files:
            try:
                # Process document
                doc_result = await custom_doc_processor.process_document(pdf_file, case_id)
                
                results.append({
                    "file_name": os.path.basename(pdf_file),
                    "file_path": pdf_file,
                    "document_id": doc_result.id,
                    "case_id": doc_result.case_id,
                    "metadata": doc_result.metadata,
                    "chunks_count": len(doc_result.chunks),
                    "processing_status": "completed",
                    "llm_provider": provider,
                    "llm_model": model
                })
                
            except Exception as e:
                errors.append({
                    "file_name": os.path.basename(pdf_file),
                    "file_path": pdf_file,
                    "error": str(e),
                    "processing_status": "failed"
                })
        
        return {
            "case_id": case_id,
            "folder_path": folder_path,
            "total_files": len(pdf_files),
            "successful_processing": len(results),
            "failed_processing": len(errors),
            "results": results,
            "errors": errors,
            "summary": {
                "total_chunks": sum(r["chunks_count"] for r in results),
                "llm_provider": provider,
                "llm_model": model,
                "processing_completed": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/process_folder_json", tags=["Document Processing"], summary="Process folder with JSON request", description="Process all PDF documents in a folder using JSON request format")
async def process_folder_json(request: Request):
    """Process all PDF documents in a folder using JSON request"""
    try:
        body = await request.json()
        folder_path = body.get("folder_path", "")
        case_id = body.get("case_id", "")
        provider = body.get("provider", "ollama")
        model = body.get("model", "mistral")
        base_url = body.get("base_url")
        api_key = body.get("api_key")
        temperature = body.get("temperature", 0.0)
        
        if not case_id:
            raise HTTPException(status_code=400, detail="case_id is required")
        
        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path is required")
        
        # Validate folder path
        if not os.path.exists(folder_path):
            raise HTTPException(status_code=400, detail=f"Folder path does not exist: {folder_path}")
        
        if not os.path.isdir(folder_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
        
        # Create LLM configuration
        llm_config = LLMConfig(
            provider=LLMProvider(provider),
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature
        )
        
        # Create document processor
        custom_doc_processor = LegalDocumentProcessor(llm_config)
        
        # Find all PDF files in the folder
        pdf_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(folder_path, file))
        
        if not pdf_files:
            raise HTTPException(status_code=400, detail=f"No PDF files found in folder: {folder_path}")
        
        # Process all documents
        results = []
        errors = []
        
        for pdf_file in pdf_files:
            try:
                # Process document
                doc_result = await custom_doc_processor.process_document(pdf_file, case_id)
                
                results.append({
                    "file_name": os.path.basename(pdf_file),
                    "file_path": pdf_file,
                    "document_id": doc_result.id,
                    "case_id": doc_result.case_id,
                    "metadata": doc_result.metadata,
                    "chunks_count": len(doc_result.chunks),
                    "processing_status": "completed",
                    "llm_provider": provider,
                    "llm_model": model
                })
                
            except Exception as e:
                errors.append({
                    "file_name": os.path.basename(pdf_file),
                    "file_path": pdf_file,
                    "error": str(e),
                    "processing_status": "failed"
                })
        
        return {
            "case_id": case_id,
            "folder_path": folder_path,
            "total_files": len(pdf_files),
            "successful_processing": len(results),
            "failed_processing": len(errors),
            "results": results,
            "errors": errors,
            "summary": {
                "total_chunks": sum(r["chunks_count"] for r in results),
                "llm_provider": provider,
                "llm_model": model,
                "processing_completed": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process folder: {str(e)}")

@app.post("/mcp/generate_demand_letter", tags=["Document Generation"], summary="Generate demand letter", description="Generate a demand letter using RAG and case data")
async def generate_demand_letter(
    case_id: str = Query(..., description="Case ID to generate letter for"),
    template_type: str = Query(default="demand_letter", description="Type of letter template to use"),
    additional_context: Dict[str, Any] = Body(default=None, description="Additional context for letter generation")
):
    """Generate demand letter using RAG and case data"""
    try:
        if additional_context is None:
            additional_context = {}
        
        # Get case data
        db_session = db.SessionLocal()
        try:
            case = db_session.query(models.Case).filter(models.Case.case_id == case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
            
            parties = db_session.query(models.Party).filter(models.Party.case_id == case_id).all()
            events = db_session.query(models.TimelineEvent).filter(models.TimelineEvent.case_id == case_id).all()
            financials = db_session.query(models.FinancialRecord).filter(models.FinancialRecord.case_id == case_id).all()
            
            # Query RAG for relevant information
            rag_queries = [
                "Summarize medical expenses and treatment details",
                "Calculate lost wages and income impact",
                "Assess pain and suffering factors",
                "Identify liability and negligence evidence"
            ]
            
            rag_results = {}
            for query in rag_queries:
                response = await rag_engine.query(query, case_id, additional_context)
                rag_results[query] = response.answer
            
            # Generate letter content
            letter_content = await _generate_letter_content(
                case, parties, events, financials, rag_results, template_type
            )
            
            return {
                "letter_content": letter_content,
                "case_id": case_id,
                "template_type": template_type,
                "rag_context": rag_results,
                "generated_at": "2024-01-01T00:00:00Z"  # Would use datetime.now().isoformat()
            }
        finally:
            db_session.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/tools", tags=["MCP"], summary="Get MCP tools", description="Get available MCP (Model Context Protocol) tools")
async def get_mcp_tools():
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

@app.get("/llm/providers", tags=["LLM"], summary="Get LLM providers", description="Get available LLM providers and their configurations")
async def get_llm_providers():
    """Return available LLM providers and their configurations"""
    return {
        "providers": [
            {
                "name": "ollama",
                "display_name": "Ollama (Local)",
                "description": "Local LLM inference using Ollama",
                "models": [
                    {"name": "mistral", "description": "Mistral 7B model"},
                    {"name": "llama2", "description": "Llama 2 model"},
                    {"name": "mixtral", "description": "Mixtral model"},
                    {"name": "codellama", "description": "Code Llama model"}
                ],
                "config": {
                    "base_url": "http://localhost:11434",
                    "requires_api_key": False,
                    "supports_temperature": True
                }
            },
            {
                "name": "openai",
                "display_name": "OpenAI (Cloud)",
                "description": "Cloud-based LLM using OpenAI API",
                "models": [
                    {"name": "gpt-4", "description": "GPT-4 model"},
                    {"name": "gpt-4-turbo", "description": "GPT-4 Turbo model"},
                    {"name": "gpt-3.5-turbo", "description": "GPT-3.5 Turbo model"}
                ],
                "config": {
                    "base_url": None,
                    "requires_api_key": True,
                    "supports_temperature": True
                }
            }
        ],
        "current_config": {
            "provider": config.llm_config.provider.value,
            "model": config.llm_config.model,
            "temperature": config.llm_config.temperature
        }
    }

@app.post("/mcp/query", tags=["MCP"], summary="MCP query", description="Execute MCP (Model Context Protocol) queries")
async def mcp_query(
    request: dict = Body(..., description="MCP query request"),
    db: Session = Depends(get_db)
):
    """Handle MCP-style queries with RAG integration"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "legal.query":
            query = params.get("query")
            case_id = params.get("case_id")
            context = params.get("context", {})
            
            if not query or not case_id:
                raise HTTPException(status_code=400, detail="Query and case_id are required")
            
            response = await rag_engine.query(query, case_id, context)
            return {
                "result": {
                    "answer": response.answer,
                    "sources": response.sources,
                    "context_used": response.context_used,
                    "case_id": case_id,
                    "query": query
                }
            }
        elif method == "legal.get_case_context":
            case_id = params.get("case_id")
            if not case_id:
                raise HTTPException(status_code=400, detail="case_id is required")
            
            case = db.query(models.Case).filter(models.Case.case_id == case_id).first()
            if not case:
                raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
            
            parties = db.query(models.Party).filter(models.Party.case_id == case_id).all()
            events = db.query(models.TimelineEvent).filter(models.TimelineEvent.case_id == case_id).all()
            financials = db.query(models.FinancialRecord).filter(models.FinancialRecord.case_id == case_id).all()
            
            return {
                "result": {
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
                    ]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
    except Exception as e:
        return {
            "result": None,
            "error": str(e)
        }

@app.post("/generate-pdf", tags=["PDF Generation"], summary="Generate PDF", description="Generate PDF from letter content using FormData")
async def generate_pdf(
    letter_content: str = Form(..., description="Letter content to convert to PDF"),
    case_id: str = Form(..., description="Case ID for the PDF filename")
):
    """Generate PDF from letter content using FormData"""
    return await _generate_pdf_internal(letter_content, case_id)

@app.post("/generate-pdf-json", tags=["PDF Generation"], summary="Generate PDF from JSON", description="Generate PDF from letter content using JSON request")
async def generate_pdf_json(request: Request):
    """Generate PDF from letter content using JSON"""
    try:
        body = await request.json()
        letter_content = body.get("letter_content", "")
        case_id = body.get("case_id", "")
        
        if not letter_content or not case_id:
            raise HTTPException(status_code=400, detail="letter_content and case_id are required")
        
        return await _generate_pdf_internal(letter_content, case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse request: {str(e)}")

async def _generate_pdf_internal(letter_content: str, case_id: str):
    """Internal function to generate PDF"""
    try:
        # Create PDF file
        pdf_filename = f"demand_letter_{case_id}.pdf"
        pdf_path = f"temp_{pdf_filename}"
        
        # Create the PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1  # Center alignment
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            leftIndent=0
        )
        
        # Build the PDF content
        story = []
        
        # Add title
        story.append(Paragraph("DEMAND LETTER", title_style))
        story.append(Spacer(1, 20))
        
        # Split content into paragraphs and add to story
        paragraphs = letter_content.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                # Handle special formatting for headers
                if paragraph.strip().startswith('[') and paragraph.strip().endswith(']'):
                    # This is a header like [LAW FIRM LETTERHEAD]
                    story.append(Paragraph(paragraph.strip(), normal_style))
                elif paragraph.strip().startswith('Re:') or paragraph.strip().startswith('Dear'):
                    # This is a formal address
                    story.append(Paragraph(paragraph.strip(), normal_style))
                elif paragraph.strip().startswith('BASED ON OUR ANALYSIS') or paragraph.strip().startswith('LIABILITY EVIDENCE') or paragraph.strip().startswith('DETAILED BREAKDOWN'):
                    # This is a section header
                    header_style = ParagraphStyle(
                        'SectionHeader',
                        parent=styles['Heading2'],
                        fontSize=14,
                        spaceAfter=10,
                        spaceBefore=15
                    )
                    story.append(Paragraph(paragraph.strip(), header_style))
                else:
                    # Regular paragraph
                    story.append(Paragraph(paragraph.strip(), normal_style))
        
        # Build the PDF
        doc.build(story)
        
        # Read the PDF file and return as bytes
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Clean up the temporary file
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except:
            pass
        
        # Return PDF as bytes with proper headers
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{pdf_filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

async def _generate_letter_content(case, parties, events, financials, rag_results, template_type):
    """Generate letter content using RAG results and case data"""
    from datetime import datetime
    
    # Extract key information from RAG results
    medical_info = rag_results.get("Summarize medical expenses and treatment details", "")
    lost_wages_info = rag_results.get("Calculate lost wages and income impact", "")
    pain_suffering_info = rag_results.get("Assess pain and suffering factors", "")
    liability_info = rag_results.get("Identify liability and negligence evidence", "")
    
    # Calculate totals from financial records
    medical_total = sum(f.amount for f in financials if f.record_type == "medical")
    lost_wages_total = sum(f.amount for f in financials if f.record_type == "lost_wages")
    pain_suffering_total = sum(f.amount for f in financials if f.record_type == "pain_suffering")
    
    # Find defendant and client
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
