# Legal AI Case Management System - Architecture Overview

## 🏗️ System Architecture

### High-Level Architecture

The Legal AI Case Management System is built as a modern, microservices-inspired architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   React App     │  │   Tailwind CSS  │  │   Axios Client  │ │
│  │   (Port 3000)   │  │   Styling       │  │   API Calls     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   FastAPI       │  │   CORS          │  │   Request/      │ │
│  │   (Port 8000)   │  │   Middleware    │  │   Response      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   MCP Server    │  │   RAG Pipeline  │  │   PDF Generator │ │
│  │   Protocol      │  │   Document Proc │  │   ReportLab     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL    │  │   ChromaDB      │  │   File System   │ │
│  │   (Cases/Data)  │  │   (Vectors)     │  │   (Documents)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Technical Implementation

### 1. Frontend Architecture (React)

#### Component Structure
```
frontend/src/
├── App.js                    # Main application component
│   ├── CaseInfo             # Case information display
│   ├── LetterGenerator      # Demand letter generation
│   ├── RAGQuery            # RAG query interface
│   └── downloadLetter       # PDF download functionality
├── index.js                 # Application entry point
└── index.css               # Global styles
```

#### Key Features
- **State Management**: React hooks for local state
- **API Integration**: Axios for HTTP requests
- **UI Framework**: Tailwind CSS for styling
- **PDF Download**: Blob-based file download
- **Error Handling**: Try-catch with fallback mechanisms

#### State Management Pattern
```javascript
// Main application state
const [caseId, setCaseId] = useState('2024-PI-001');
const [caseData, setCaseData] = useState(null);
const [letterContent, setLetterContent] = useState('');
const [ragQuery, setRagQuery] = useState('');
const [ragResponse, setRagResponse] = useState('');
```

### 2. Backend Architecture (FastAPI)

#### Application Structure
```
app/
├── main.py                  # FastAPI application entry point
├── models.py               # SQLAlchemy ORM models
├── db.py                   # Database connection management
├── rag_pipeline.py         # RAG engine implementation
├── llm_factory.py          # LLM provider abstraction
├── config.py               # Configuration management
├── schemas.py              # Pydantic data validation
└── mcp_server.py           # MCP protocol implementation
```

#### Key Design Patterns

1. **Dependency Injection**
   ```python
   def get_db():
       db_session = db.SessionLocal()
       try:
           yield db_session
       finally:
           db_session.close()
   ```

2. **Service Layer Pattern**
   ```python
   class LegalRAGEngine:
       def __init__(self):
           self.embeddings = HuggingFaceEmbeddings(...)
           self.llm = LLMFactory.create_llm(...)
   ```

3. **Factory Pattern**
   ```python
   class LLMFactory:
       @staticmethod
       def create_llm(provider: str, model: str, **kwargs):
           if provider == "ollama":
               return Ollama(model=model, **kwargs)
   ```

### 3. RAG Pipeline Architecture

#### Document Processing Flow
```
PDF Document → Text Extraction → Chunking → Embedding → Vector Storage
     ↓              ↓              ↓           ↓            ↓
  PyPDF2       Raw Text      Semantic     Sentence    ChromaDB
              Processing      Chunks     Transformers
```

#### Query Processing Flow
```
Natural Language Query → Embedding → Vector Search → Context Assembly → LLM Generation
         ↓                ↓            ↓              ↓               ↓
    User Input      Query Vector   Similar Chunks   Retrieved      Response
                                      from DB       Context       with Sources
```

#### Implementation Details

1. **Document Chunking Strategy**
   ```python
   def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200):
       chunks = []
       start = 0
       while start < len(text):
           end = start + chunk_size
           chunk = text[start:end]
           chunks.append(chunk)
           start = end - overlap
       return chunks
   ```

2. **Vector Search Implementation**
   ```python
   def query_documents(self, query: str, case_id: str, context: Dict = None):
       # Create vector store for case
       vectordb = Chroma.from_documents(
           documents=self.get_case_documents(case_id),
           embedding=self.embeddings
       )
       
       # Perform similarity search
       retriever = vectordb.as_retriever(
           search_type="similarity",
           search_kwargs={"k": 5}
       )
       
       # Retrieve relevant chunks
       relevant_chunks = retriever.get_relevant_documents(query)
       
       # Generate response with context
       response = self.llm(f"Context: {relevant_chunks}\nQuery: {query}")
       return response
   ```

### 4. Database Architecture

#### Entity Relationship Diagram
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Cases    │    │   Parties   │    │   Events    │
│             │    │             │    │             │
│ case_id (PK)│◄──►│ case_id (FK)│    │ case_id (FK)│
│ case_type   │    │ party_type  │    │ event_date  │
│ status      │    │ name        │    │ description │
│ summary     │    │ contact     │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Financial   │    │ Documents   │    │ Timeline    │
│ Records     │    │             │    │ Events      │
│             │    │             │    │             │
│ case_id (FK)│    │ case_id (FK)│    │ case_id (FK)│
│ record_type │    │ doc_type    │    │ event_type  │
│ amount      │    │ file_path   │    │ timestamp   │
│ date        │    │ metadata    │    │ details     │
└─────────────┘    └─────────────┘    └─────────────┘
```

#### Database Models
```python
class Case(Base):
    __tablename__ = "cases"
    case_id = Column(String, primary_key=True)
    case_type = Column(String)
    status = Column(String)
    case_summary = Column(String)
    date_filed = Column(Date)
    attorney_id = Column(Integer)

class Party(Base):
    __tablename__ = "parties"
    id = Column(Integer, primary_key=True)
    case_id = Column(String, ForeignKey("cases.case_id"))
    party_type = Column(String)  # plaintiff, defendant, etc.
    name = Column(String)
    contact_info = Column(String)
```

### 5. MCP (Model Context Protocol) Integration

#### Protocol Implementation
```python
class LegalMCPServer:
    def __init__(self):
        self.rag_engine = LegalRAGEngine()
        self.doc_processor = LegalDocumentProcessor()
    
    async def handle_query(self, request: dict):
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "legal.query":
            return await self.rag_engine.query(
                params["query"], 
                params["case_id"], 
                params.get("context", {})
            )
        elif method == "legal.generate_demand_letter":
            return await self.generate_demand_letter(
                params["case_id"],
                params.get("template_type", "demand_letter"),
                params.get("additional_context", {})
            )
```

#### Available MCP Tools
1. **legal.query** - Query legal documents using RAG
2. **legal.analyze_document** - Analyze and process legal documents
3. **legal.generate_demand_letter** - Generate demand letters
4. **legal.get_case_context** - Get comprehensive case context

### 6. PDF Generation Architecture

#### PDF Generation Flow
```
Letter Content → ReportLab Processing → PDF Document → File Response
      ↓                ↓                    ↓              ↓
   Text Data      Document Builder      PDF Bytes     HTTP Response
```

#### Implementation Details
```python
async def generate_pdf(letter_content: str, case_id: str):
    # Create PDF document
    pdf_filename = f"demand_letter_{case_id}.pdf"
    pdf_path = f"temp_{pdf_filename}"
    
    # Build PDF with ReportLab
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        alignment=1
    )
    
    # Build content
    story = []
    story.append(Paragraph("DEMAND LETTER", title_style))
    
    # Process letter content
    paragraphs = letter_content.split('\n\n')
    for paragraph in paragraphs:
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), styles['Normal']))
    
    # Generate PDF
    doc.build(story)
    
    # Return as file response
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{pdf_filename}"'}
    )
```

## 🔄 Data Flow Patterns

### 1. Document Processing Flow
```
1. User uploads PDF → 2. Backend receives file → 3. PyPDF2 extracts text
4. Text is chunked → 5. Chunks are embedded → 6. Stored in ChromaDB
7. Metadata is saved → 8. Success response sent
```

### 2. RAG Query Flow
```
1. User submits query → 2. Query is embedded → 3. Vector search performed
4. Relevant chunks retrieved → 5. Context assembled → 6. LLM generates response
7. Response returned with sources → 8. Frontend displays result
```

### 3. Demand Letter Generation Flow
```
1. User selects case → 2. RAG queries executed → 3. Context gathered
4. LLM generates letter → 5. Content returned → 6. User can download PDF
7. PDF generated → 8. File downloaded
```

## 🛡️ Security Considerations

### 1. Input Validation
- **Pydantic Schemas**: All API inputs validated with Pydantic
- **File Upload Security**: File type and size validation
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

### 2. CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Error Handling
- **Graceful Degradation**: Fallback mechanisms for failed operations
- **Detailed Logging**: Comprehensive error logging for debugging
- **User-Friendly Messages**: Clear error messages for end users

## 📊 Performance Considerations

### 1. Caching Strategy
- **Vector Store Caching**: ChromaDB provides in-memory caching
- **Database Connection Pooling**: SQLAlchemy connection pooling
- **LLM Response Caching**: Optional caching for repeated queries

### 2. Scalability Patterns
- **Stateless Design**: Backend services are stateless
- **Horizontal Scaling**: Multiple backend instances possible
- **Database Optimization**: Indexed queries for performance

### 3. Resource Management
- **Memory Management**: Proper cleanup of temporary files
- **Connection Pooling**: Efficient database connection management
- **Async Operations**: Non-blocking I/O operations

## 🔧 Configuration Management

### Environment-Based Configuration
```python
class Settings(BaseSettings):
    database_url: str = "postgresql://localhost/legal_ai_db"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    class Config:
        env_file = ".env"
```

### Feature Flags
```python
class FeatureFlags:
    ENABLE_PDF_GENERATION = True
    ENABLE_RAG_QUERIES = True
    ENABLE_MCP_PROTOCOL = True
    ENABLE_DOCUMENT_PROCESSING = True
```

## 🧪 Testing Strategy

### 1. Unit Testing
- **Backend Tests**: pytest for API endpoints
- **Frontend Tests**: Jest for React components
- **RAG Tests**: Mock-based testing for document processing

### 2. Integration Testing
- **API Integration**: End-to-end API testing
- **Database Integration**: Database operation testing
- **PDF Generation**: PDF output validation

### 3. Performance Testing
- **Load Testing**: Multiple concurrent users
- **Document Processing**: Large file processing
- **RAG Query Performance**: Query response times

## 🚀 Deployment Architecture

### Development Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Dev     │    │   FastAPI Dev   │    │   PostgreSQL    │
│   Server        │    │   Server        │    │   Local         │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Production Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Gunicorn      │    │   PostgreSQL    │
│   (Load Balancer)│◄──►│   (FastAPI)     │◄──►│   (Production)  │
│   (Port 80/443) │    │   (Port 8000)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   ChromaDB      │
                       │   (Persistent)  │
                       │   Storage       │
                       └─────────────────┘
```

## 📈 Monitoring and Observability

### 1. Logging Strategy
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Log Aggregation**: Centralized log collection

### 2. Metrics Collection
- **API Metrics**: Request/response times, error rates
- **RAG Metrics**: Query performance, retrieval accuracy
- **System Metrics**: CPU, memory, disk usage

### 3. Health Checks
- **Database Health**: Connection status
- **RAG Health**: Vector store availability
- **LLM Health**: Model availability

## 🔮 Future Enhancements

### 1. Advanced RAG Features
- **Multi-Modal RAG**: Support for images and tables
- **Hybrid Search**: Combining semantic and keyword search
- **Query Expansion**: Automatic query enhancement

### 2. Enhanced LLM Integration
- **Multi-Model Support**: Support for multiple LLM providers
- **Fine-Tuning**: Domain-specific model fine-tuning
- **Chain-of-Thought**: Advanced reasoning capabilities

### 3. Advanced Document Processing
- **OCR Integration**: Handwritten document processing
- **Table Extraction**: Structured data extraction
- **Legal Citation Parsing**: Automatic citation extraction

---

This architecture provides a solid foundation for a scalable, maintainable legal AI system that can evolve with changing requirements and technological advances. 