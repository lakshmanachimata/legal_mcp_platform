import os
import fitz  # PyMuPDF
from typing import List, Dict, Optional, Any
from datetime import datetime
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .models import Case, Party, TimelineEvent, FinancialRecord
from .db import SessionLocal
from .config import config
from .llm_factory import LLMFactory

# Legal document processing prompts
LEGAL_ANALYSIS_PROMPT = """
Analyze the following legal document excerpt and extract key information:
{text}
Identify:
1. Document type
2. Parties involved
3. Key dates
4. Legal citations
5. Important facts
6. Monetary amounts
7. Medical information
8. Liability factors
"""

RESPONSE_GENERATION_PROMPT = """
Based on the retrieved context and case information, provide a detailed response:
Query: {query}
Case Context: {case_context}
Retrieved Documents: {documents}
Requirements:
1. Cite relevant documents and sections
2. Reference applicable legal precedents
3. Provide factual support for conclusions
4. Note any important caveats or limitations
5. Include specific amounts and dates when available
"""

class CaseDocument(BaseModel):
    id: str
    case_id: str
    metadata: Dict[str, Any]
    chunks: List[str]

class DocumentChunk(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    context_used: Dict[str, Any]

class LegalDocumentProcessor:
    def __init__(self, llm_config=None):
        if llm_config is None:
            llm_config = config.llm_config
        
        self.llm = LLMFactory.create_llm(llm_config)
        self.analysis_prompt = PromptTemplate(
            template=LEGAL_ANALYSIS_PROMPT,
            input_variables=["text"]
        )

    async def process_document(self, file_path: str, case_id: str) -> CaseDocument:
        """Process a legal document with enhanced metadata extraction"""
        text = self._extract_text(file_path)
        
        # Analyze document structure and content
        analysis = self._analyze_document(text)
        
        # Create semantic chunks based on legal document structure
        chunks = self._create_legal_chunks(text, analysis)
        
        # Store chunks in vector database
        doc_id = await self._store_chunks(chunks, case_id)
        
        return CaseDocument(
            id=doc_id,
            case_id=case_id,
            metadata=analysis,
            chunks=[chunk.id for chunk in chunks]
        )

    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF with structure preservation"""
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                # Use simple text extraction that works reliably
                text += page.get_text() + "\n"
        return text.strip()

    def _analyze_document(self, text: str) -> Dict:
        """Analyze document content using LLM"""
        analysis = self.llm.invoke(self.analysis_prompt.format(text=text[:2000]))  # Limit for analysis
        return self._parse_analysis(analysis)

    def _parse_analysis(self, analysis: str) -> Dict:
        """Parse LLM analysis into structured format"""
        # Simple parsing - in production, use more sophisticated parsing
        return {
            "document_type": "legal_document",
            "parties": [],
            "citations": [],
            "monetary_amounts": [],
            "medical_info": [],
            "liability_factors": []
        }

    def _create_legal_chunks(self, text: str, analysis: Dict) -> List[DocumentChunk]:
        """Create semantic chunks based on legal document structure"""
        # Use custom chunking based on document type and structure
        chunk_size = 1000
        overlap = 200
        
        if analysis.get("document_type") == "legal_brief":
            chunk_size = 1500  # Larger chunks for briefs
        elif analysis.get("document_type") == "contract":
            chunk_size = 800   # Smaller chunks for contracts
            
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ".", " "]
        )
        
        raw_chunks = splitter.split_text(text)
        return [
            DocumentChunk(
                id=f"chunk_{i}",
                text=chunk,
                metadata={
                    "document_type": analysis.get("document_type", "legal_document"),
                    "parties": analysis.get("parties", []),
                    "citations": self._extract_citations(chunk),
                    "chunk_index": i
                }
            )
            for i, chunk in enumerate(raw_chunks)
        ]

    def _extract_citations(self, text: str) -> List[str]:
        """Extract legal citations from text"""
        # Simple citation extraction - in production, use regex patterns
        citations = []
        # Look for common citation patterns
        import re
        patterns = [
            r'\d+ U\.S\. \d+',
            r'\d+ F\.\d+ \d+',
            r'\d+ Cal\.\d+ \d+',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        return citations

    def _clean_metadata(self, metadata: Dict) -> Dict:
        """Clean metadata to be compatible with ChromaDB"""
        cleaned = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                cleaned[key] = value
            elif isinstance(value, list):
                # Convert lists to strings for ChromaDB compatibility
                cleaned[key] = ", ".join(str(item) for item in value)
            else:
                # Convert other types to string
                cleaned[key] = str(value)
        return cleaned

    async def _store_chunks(self, chunks: List[DocumentChunk], case_id: str) -> str:
        """Store document chunks in vector database"""
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        texts = [chunk.text for chunk in chunks]
        metadatas = [self._clean_metadata(chunk.metadata) for chunk in chunks]
        
        # Ensure directory exists
        os.makedirs(os.path.join(config.chroma_dir, case_id), exist_ok=True)
        
        vectordb = Chroma.from_texts(
            texts,
            embeddings,
            metadatas=metadatas,
            persist_directory=os.path.join(config.chroma_dir, case_id)
        )
        vectordb.persist()
        
        # Store in SQL database for metadata querying
        doc_id = await self._store_chunks_in_db(case_id, chunks)
        return doc_id

    async def _store_chunks_in_db(self, case_id: str, chunks: List[DocumentChunk]) -> str:
        """Store chunk metadata in SQL database"""
        # This would typically store in a DocumentChunk table
        # For now, return a simple ID
        return f"doc_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

class LegalRAGEngine:
    def __init__(self, llm_config=None):
        if llm_config is None:
            llm_config = config.llm_config
        
        self.llm = LLMFactory.create_llm(llm_config)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.embedding_model
        )
        self.response_prompt = PromptTemplate(
            template=RESPONSE_GENERATION_PROMPT,
            input_variables=["query", "case_context", "documents"]
        )

    async def query(self, query: str, case_id: str, context: Dict) -> QueryResponse:
        """Query documents with enhanced context awareness"""
        
        # Check if this is a system-wide query about cases
        if self._is_system_query(query):
            return await self._handle_system_query(query)
        
        # Get case context from database
        case_context = await self._get_case_context(case_id)
        
        # Check if vector store exists for this case
        vector_store_path = os.path.join(config.chroma_dir, case_id)
        print(f"🔍 Checking vector store path: {vector_store_path}")
        print(f"🔍 Path exists: {os.path.exists(vector_store_path)}")
        
        if not os.path.exists(vector_store_path):
            print(f"❌ Vector store not found for case {case_id}")
            # No documents processed yet, return response based on case context only
            return await self._generate_response_from_context_only(
                query=query,
                case_context=case_context,
                user_context=context
            )
        
        # Load case-specific vector store
        try:
            vectordb = Chroma(
                persist_directory=vector_store_path,
                embedding_function=self.embeddings
            )
            
            # Retrieve relevant chunks
            retriever = vectordb.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 5
                }
            )
            print(f"🔍 Retrieving documents for query: '{query}'")
            relevant_chunks = retriever.get_relevant_documents(query)
            print(f"🔍 Retrieved {len(relevant_chunks)} chunks")
            
            if len(relevant_chunks) > 0:
                print(f"🔍 First chunk preview: {relevant_chunks[0].page_content[:100]}...")
            else:
                print("❌ No chunks retrieved")
            
            # Generate response
            response = await self._generate_response(
                query=query,
                chunks=relevant_chunks,
                case_context=case_context,
                user_context=context
            )
            
            return response
        except Exception as e:
            # Fallback to context-only response
            return await self._generate_response_from_context_only(
                query=query,
                case_context=case_context,
                user_context=context
            )

    async def _generate_response_from_context_only(
        self,
        query: str,
        case_context: Dict,
        user_context: Dict
    ) -> QueryResponse:
        """Generate response when no documents are available"""
        formatted_context = self._format_context(case_context, user_context)
        
        # Create a simple response based on case context
        response_text = f"""
Based on the case information available:

Query: {query}

Case Summary: {case_context.get('case', {}).get('case_summary', 'No summary available')}

Financial Information:
{self._format_financials(case_context.get('financials', []))}

Parties Involved:
{self._format_parties(case_context.get('parties', []))}

Note: No legal documents have been processed for this case yet. The response is based on case metadata only.
        """
        
        return QueryResponse(
            answer=response_text.strip(),
            sources=[],
            context_used=formatted_context
        )

    def _format_financials(self, financials: List[Dict]) -> str:
        """Format financial information"""
        if not financials:
            return "No financial records available"
        
        formatted = []
        for f in financials:
            formatted.append(f"- {f.get('record_type', 'Unknown')}: ${f.get('amount', 0):,} - {f.get('description', '')}")
        return "\n".join(formatted)

    def _format_parties(self, parties: List[Dict]) -> str:
        """Format party information"""
        if not parties:
            return "No parties information available"
        
        formatted = []
        for p in parties:
            formatted.append(f"- {p.get('party_type', 'Unknown')}: {p.get('name', 'Unknown')}")
        return "\n".join(formatted)

    def _is_system_query(self, query: str) -> bool:
        """Check if query is about system-wide case information"""
        system_keywords = [
            'number of cases', 'total cases', 'all cases', 'case count',
            'pending cases', 'active cases', 'case status', 'system cases',
            'how many cases', 'case summary', 'overview', 'dashboard',
            'case list', 'case inventory', 'case management', 'overall cases',
            'system overview', 'case overview', 'all cases details',
            'case statistics', 'case summary', 'case details', 'dates',
            'timeline', 'events', 'filing dates'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in system_keywords)

    async def _handle_system_query(self, query: str) -> QueryResponse:
        """Handle system-wide queries about cases"""
        try:
            db = SessionLocal()
            
            # Get all cases with detailed information
            cases = db.query(Case).all()
            
            # Get detailed case information including parties, events, and financials
            detailed_cases = []
            for case in cases:
                parties = db.query(Party).filter(Party.case_id == case.case_id).all()
                events = db.query(TimelineEvent).filter(TimelineEvent.case_id == case.case_id).all()
                financials = db.query(FinancialRecord).filter(FinancialRecord.case_id == case.case_id).all()
                
                # Calculate total financial amount
                total_amount = sum(f.amount for f in financials) if financials else 0
                
                # Get timeline events with dates
                timeline_events = []
                for event in events:
                    timeline_events.append({
                        'date': event.event_date.strftime('%Y-%m-%d') if event.event_date else 'Unknown',
                        'description': event.description
                    })
                
                detailed_cases.append({
                    'case_id': case.case_id,
                    'case_type': case.case_type,
                    'status': case.status,
                    'date_filed': case.date_filed.strftime('%Y-%m-%d') if case.date_filed else 'Unknown',
                    'summary': case.case_summary,
                    'parties_count': len(parties),
                    'events_count': len(events),
                    'financials_count': len(financials),
                    'total_amount': total_amount,
                    'parties': [{'type': p.party_type, 'name': p.name} for p in parties],
                    'recent_events': [e.description for e in events[-3:]] if events else [],
                    'timeline_events': timeline_events,
                    'financial_summary': f"${total_amount:,}" if total_amount > 0 else "No financial records"
                })
            
            # Get case statistics
            total_cases = len(cases)
            active_cases = len([c for c in cases if c.status == 'Active'])
            pending_cases = len([c for c in cases if c.status in ['Active', 'Pending']])
            total_financial_amount = sum(c['total_amount'] for c in detailed_cases)
            
            # Generate response based on query type
            if 'number' in query.lower() or 'count' in query.lower() or 'total' in query.lower():
                response_text = f"""
**Case System Overview**

📊 **Total Cases**: {total_cases}
📈 **Active Cases**: {active_cases}
⏳ **Pending Cases**: {pending_cases}
💰 **Total Financial Amount**: ${total_financial_amount:,}

**Case Breakdown by Status:**
- Active: {active_cases} cases
- Pending: {len([c for c in cases if c.status == 'Pending'])} cases
- Closed: {len([c for c in cases if c.status == 'Closed'])} cases
- Other: {len([c for c in cases if c.status not in ['Active', 'Pending', 'Closed']])} cases
                """
            elif 'dates' in query.lower() or 'timeline' in query.lower() or 'events' in query.lower():
                # Show case details with focus on dates and timeline
                case_details = []
                for case in detailed_cases:
                    parties_list = ", ".join([f"{p['type']}: {p['name']}" for p in case['parties'][:3]])
                    
                    # Format timeline events with dates
                    timeline_text = ""
                    if case['timeline_events']:
                        timeline_text = "\n".join([
                            f"  • {event['date']}: {event['description']}"
                            for event in case['timeline_events']
                        ])
                    else:
                        timeline_text = "No timeline events"
                    
                    case_details.append(f"""
**{case['case_id']}** - {case['case_type']} ({case['status']})
- **Filing Date**: {case['date_filed']}
- **Parties**: {parties_list}
- **Timeline Events**:
{timeline_text}
                    """.strip())
                
                response_text = f"""
**Case Timeline Overview**

📊 **Total Cases**: {total_cases}
📈 **Active Cases**: {active_cases}
⏳ **Pending Cases**: {pending_cases}

**Case Dates and Timeline:**
{chr(10).join(case_details)}
                """
            elif 'details' in query.lower() or 'comprehensive' in query.lower():
                # Show comprehensive case details
                case_details = []
                for case in detailed_cases:
                    parties_list = ", ".join([f"{p['type']}: {p['name']}" for p in case['parties'][:3]])
                    
                    # Format timeline events with dates
                    timeline_text = ""
                    if case['timeline_events']:
                        timeline_text = "\n".join([
                            f"  • {event['date']}: {event['description']}"
                            for event in case['timeline_events']
                        ])
                    else:
                        timeline_text = "No timeline events"
                    
                    case_details.append(f"""
**{case['case_id']}** - {case['case_type']} ({case['status']})
- **Filed**: {case['date_filed']}
- **Summary**: {case['summary']}
- **Parties**: {parties_list}
- **Timeline Events**:
{timeline_text}
- **Financial Summary**: {case['financial_summary']}
                    """.strip())
                
                response_text = f"""
**Comprehensive Case System Overview**

📊 **Total Cases**: {total_cases}
📈 **Active Cases**: {active_cases}
⏳ **Pending Cases**: {pending_cases}
💰 **Total Financial Amount**: ${total_financial_amount:,}

**Detailed Case Information:**
{chr(10).join(case_details)}
                """
            else:
                # Show standard case list
                case_list = "\n".join([
                    f"• **{case['case_id']}** - {case['case_type']} ({case['status']}) - Filed: {case['date_filed']} - {case['financial_summary']}"
                    for case in detailed_cases
                ])
                
                response_text = f"""
**Case System Overview**

📊 **Total Cases**: {total_cases}
📈 **Active Cases**: {active_cases}
⏳ **Pending Cases**: {pending_cases}
💰 **Total Financial Amount**: ${total_financial_amount:,}

**All Cases:**
{case_list}

**Summary**: The system contains {total_cases} total cases with {active_cases} currently active and {pending_cases} pending resolution. Total financial amount across all cases is ${total_financial_amount:,}.
                """
            
            db.close()
            
            return QueryResponse(
                answer=response_text.strip(),
                sources=[{'type': 'system_query', 'query': query, 'total_cases': total_cases, 'total_amount': total_financial_amount}],
                context_used={'query_type': 'system_overview', 'cases_analyzed': total_cases}
            )
            
        except Exception as e:
            return QueryResponse(
                answer=f"Error retrieving system information: {str(e)}",
                sources=[],
                context_used={'error': str(e)}
            )

    async def _get_case_context(self, case_id: str) -> Dict[str, Any]:
        """Get case context from database"""
        db = SessionLocal()
        try:
            case = db.query(Case).filter(Case.case_id == case_id).first()
            if not case:
                return {}
            
            parties = db.query(Party).filter(Party.case_id == case_id).all()
            events = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()
            financials = db.query(FinancialRecord).filter(FinancialRecord.case_id == case_id).all()
            
            return {
                "case": {
                    "case_id": case.case_id,
                    "case_type": case.case_type,
                    "status": case.status,
                    "case_summary": case.case_summary
                },
                "parties": [
                    {
                        "party_type": p.party_type,
                        "name": p.name,
                        "contact_info": p.contact_info
                    } for p in parties
                ],
                "events": [
                    {
                        "event_date": e.event_date.isoformat() if e.event_date else None,
                        "description": e.description
                    } for e in events
                ],
                "financials": [
                    {
                        "record_type": f.record_type,
                        "amount": f.amount,
                        "description": f.description
                    } for f in financials
                ]
            }
        finally:
            db.close()

    async def _generate_response(
        self,
        query: str,
        chunks: List[Document],
        case_context: Dict,
        user_context: Dict
    ) -> QueryResponse:
        """Generate response with citations and context"""
        # Format chunks and context for prompt
        formatted_chunks = self._format_chunks_for_prompt(chunks)
        formatted_context = self._format_context(case_context, user_context)
        
        # Generate response using LLM
        response_text = self.llm.invoke(
            self.response_prompt.format(
                query=query,
                case_context=formatted_context,
                documents=formatted_chunks
            )
        )
        
        return QueryResponse(
            answer=response_text,
            sources=[chunk.metadata for chunk in chunks],
            context_used=formatted_context
        )

    def _format_chunks_for_prompt(self, chunks: List[Document]) -> str:
        """Format chunks for prompt input"""
        formatted = []
        for i, chunk in enumerate(chunks):
            formatted.append(f"Document {i+1}:\n{chunk.page_content}\n")
        return "\n".join(formatted)

    def _format_context(self, case_context: Dict, user_context: Dict) -> Dict[str, Any]:
        """Format context for prompt"""
        return {
            "case_info": case_context.get("case", {}),
            "parties": case_context.get("parties", []),
            "events": case_context.get("events", []),
            "financials": case_context.get("financials", []),
            "user_context": user_context
        }

    def _create_filters(self, context: Dict) -> Dict:
        """Create filters for vector store query"""
        filters = {}
        if "document_type" in context:
            filters["document_type"] = context["document_type"]
        if "date_range" in context:
            filters["date"] = context["date_range"]
        return filters

# Database helper functions
async def get_case_context(case_id: str) -> Dict[str, Any]:
    """Get case context from database"""
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.case_id == case_id).first()
        if not case:
            return {}
        
        parties = db.query(Party).filter(Party.case_id == case_id).all()
        events = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id).all()
        financials = db.query(FinancialRecord).filter(FinancialRecord.case_id == case_id).all()
        
        return {
            "case": case,
            "parties": parties,
            "events": events,
            "financials": financials
        }
    finally:
        db.close()

async def store_document_chunks(case_id: str, chunks: List[DocumentChunk]) -> str:
    """Store document chunks in database"""
    # This would typically store in a DocumentChunk table
    # For now, return a simple ID
    return f"doc_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

if __name__ == "__main__":
    print("This module should be imported and used via the MCP API server.")
