# ✅ LLM Provider Support - Ollama & OpenAI Integration

## 🎯 **Enhancement Summary**

The app now supports both **local Ollama** and **cloud OpenAI** providers, allowing users to choose their preferred LLM via form arguments. The system provides flexible configuration options for different use cases.

## 🔧 **New Features Added**

### **1. Configuration System**
- **`app/config.py`**: Centralized configuration management
- **`app/llm_factory.py`**: Factory pattern for LLM initialization
- **Environment Variables**: Support for configuration via environment variables

### **2. LLM Provider Support**
- **Ollama (Local)**: Local LLM inference with customizable models
- **OpenAI (Cloud)**: Cloud-based LLM using OpenAI API
- **Flexible Configuration**: Model, temperature, API keys, base URLs

### **3. New API Endpoints**

#### **RAG Query with Provider Selection**
```http
POST /rag/query-with-provider
```
**Form Parameters:**
- `query`: Natural language query
- `case_id`: Case identifier (optional for system queries)
- `provider`: "ollama" or "openai"
- `model`: Model name (e.g., "mistral", "gpt-4")
- `base_url`: Ollama base URL (optional)
- `api_key`: OpenAI API key (required for OpenAI)
- `temperature`: LLM temperature (0.0-1.0)

#### **Document Processing with Provider Selection**
```http
POST /rag/process_document-with-provider
```
**Form Parameters:**
- `file`: Document file to process
- `case_id`: Case identifier
- `provider`: "ollama" or "openai"
- `model`: Model name
- `base_url`: Ollama base URL (optional)
- `api_key`: OpenAI API key (required for OpenAI)
- `temperature`: LLM temperature

#### **LLM Providers Information**
```http
GET /llm/providers
```
**Response**: Available providers, models, and configurations

## 🧪 **Testing Results**

### **✅ Test 1: LLM Providers Endpoint**
```bash
curl -X GET http://localhost:8000/llm/providers
```
**Response:**
```json
{
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
        "requires_api_key": false,
        "supports_temperature": true
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
        "base_url": null,
        "requires_api_key": true,
        "supports_temperature": true
      }
    }
  ],
  "current_config": {
    "provider": "ollama",
    "model": "mistral",
    "temperature": 0.0
  }
}
```

### **✅ Test 2: RAG Query with Ollama**
```bash
curl -X POST http://localhost:8000/rag/query-with-provider \
  -F "query=show me all cases with their dates" \
  -F "case_id=system" \
  -F "provider=ollama" \
  -F "model=mistral"
```
**Response:**
```json
{
  "answer": "**Case Timeline Overview**\n\n📊 **Total Cases**: 3\n📈 **Active Cases**: 3\n⏳ **Pending Cases**: 3\n\n**Case Dates and Timeline:**\n**2024-PI-001** - Personal Injury (Active)\n- **Filing Date**: 2024-01-15\n- **Parties**: plaintiff: John Smith, defendant: ABC Insurance Company\n- **Timeline Events**:\n  • 2024-01-10: Motor vehicle accident occurred\n  • 2024-01-15: Case filed with court\n  • 2024-02-01: Initial discovery served\n**2024-PI-002** - Medical Malpractice (Active)\n- **Filing Date**: 2024-02-20\n- **Parties**: plaintiff: Sarah Johnson, defendant: City General Hospital\n- **Timeline Events**:\n  • 2024-02-15: Surgical procedure performed\n  • 2024-02-20: Case filed with court\n  • 2024-03-05: Medical records subpoenaed\n**2024-PI-003** - Slip and Fall (Active)\n- **Filing Date**: 2024-03-10\n- **Parties**: plaintiff: Michael Brown, defendant: Mall Management LLC\n- **Timeline Events**:\n  • 2024-03-05: Slip and fall accident occurred\n  • 2024-03-10: Case filed with court\n  • 2024-03-25: Site inspection completed",
  "sources": [{"type": "system_query", "query": "show me all cases with their dates", "total_cases": 3, "total_amount": 231000}],
  "context_used": {"query_type": "system_overview", "cases_analyzed": 3},
  "case_id": "system",
  "query": "show me all cases with their dates",
  "llm_provider": "ollama",
  "llm_model": "mistral"
}
```

### **✅ Test 3: Document Processing with Ollama**
```bash
curl -X POST http://localhost:8000/rag/process_document-with-provider \
  -F "file=@test_doc.txt" \
  -F "case_id=2024-PI-001" \
  -F "provider=ollama" \
  -F "model=mistral"
```
**Response:**
```json
{
  "document_id": "doc_2024-PI-001_20250803_000833",
  "case_id": "2024-PI-001",
  "metadata": {
    "document_type": "legal_document",
    "parties": [],
    "citations": [],
    "monetary_amounts": [],
    "medical_info": [],
    "liability_factors": []
  },
  "chunks_count": 1,
  "processing_status": "completed",
  "llm_provider": "ollama",
  "llm_model": "mistral"
}
```

## 🔄 **How It Works**

### **1. Configuration Management**
```python
# app/config.py
class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "mistral"
    base_url: Optional[str] = "http://localhost:11434"
    api_key: Optional[str] = None
    temperature: float = 0.0

class AppConfig:
    def __init__(self):
        self.llm_config = LLMConfig(
            provider=LLMProvider(os.getenv("LLM_PROVIDER", "ollama")),
            model=os.getenv("LLM_MODEL", "mistral"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.0"))
        )
```

### **2. LLM Factory Pattern**
```python
# app/llm_factory.py
class LLMFactory:
    @staticmethod
    def create_llm(config: LLMConfig):
        if config.provider == LLMProvider.OLLAMA:
            base_url = config.base_url or "http://localhost:11434"
            return Ollama(
                model=config.model,
                base_url=base_url,
                temperature=config.temperature
            )
        elif config.provider == LLMProvider.OPENAI:
            if not config.api_key:
                raise ValueError("OpenAI API key is required")
            return ChatOpenAI(
                model=config.model,
                api_key=config.api_key,
                temperature=config.temperature
            )
```

### **3. RAG Engine Integration**
```python
# app/rag_pipeline.py
class LegalRAGEngine:
    def __init__(self, llm_config=None):
        if llm_config is None:
            llm_config = config.llm_config
        
        self.llm = LLMFactory.create_llm(llm_config)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.embedding_model
        )
```

### **4. API Endpoint Implementation**
```python
@app.post("/rag/query-with-provider")
async def rag_query_with_provider(
    query: str = Form(...),
    case_id: str = Form(default=None),
    provider: str = Form(default="ollama"),
    model: str = Form(default="mistral"),
    base_url: Optional[str] = Form(default=None),
    api_key: Optional[str] = Form(default=None),
    temperature: float = Form(default=0.0),
    context: Dict[str, Any] = Body(default={})
):
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
```

## 📋 **Available Providers**

### **🔧 Ollama (Local)**
- **Models**: mistral, llama2, mixtral, codellama
- **Base URL**: http://localhost:11434 (default)
- **API Key**: Not required
- **Use Case**: Local development, privacy-sensitive applications

### **☁️ OpenAI (Cloud)**
- **Models**: gpt-4, gpt-4-turbo, gpt-3.5-turbo
- **Base URL**: None (uses OpenAI API)
- **API Key**: Required
- **Use Case**: Production applications, advanced capabilities

## 🎯 **Usage Examples**

### **Ollama Query**
```bash
curl -X POST http://localhost:8000/rag/query-with-provider \
  -F "query=overall cases details" \
  -F "case_id=system" \
  -F "provider=ollama" \
  -F "model=mistral"
```

### **OpenAI Query**
```bash
curl -X POST http://localhost:8000/rag/query-with-provider \
  -F "query=overall cases details" \
  -F "case_id=system" \
  -F "provider=openai" \
  -F "model=gpt-4" \
  -F "api_key=your-openai-api-key"
```

### **Document Processing with Ollama**
```bash
curl -X POST http://localhost:8000/rag/process_document-with-provider \
  -F "file=@document.pdf" \
  -F "case_id=2024-PI-001" \
  -F "provider=ollama" \
  -F "model=mistral"
```

## 🎯 **Benefits**

### **✅ Flexibility**
- **Multiple Providers**: Choose between local and cloud LLMs
- **Model Selection**: Different models for different use cases
- **Configuration Options**: Temperature, API keys, base URLs

### **✅ User Control**
- **Form Arguments**: Easy provider selection via form parameters
- **Environment Variables**: Configuration via environment variables
- **Runtime Selection**: Choose provider per request

### **✅ Scalability**
- **Local Development**: Use Ollama for development
- **Production**: Use OpenAI for production
- **Hybrid Approach**: Mix providers based on needs

### **✅ Cost Optimization**
- **Local Processing**: Free with Ollama
- **Cloud Processing**: Pay-per-use with OpenAI
- **Flexible Deployment**: Choose based on requirements

## 🎉 **Result**

The app now supports **both Ollama and OpenAI providers** with:

- ✅ **Flexible Configuration**: Environment variables and form arguments
- ✅ **Multiple Models**: Various models for different use cases
- ✅ **Easy Selection**: Simple form parameters for provider choice
- ✅ **Comprehensive API**: Query and document processing with provider selection
- ✅ **Provider Information**: Endpoint to get available providers and models

**Users can now choose their preferred LLM provider via form arguments! 🎯✨**

### **📊 Current Support**

| Provider | Type | Models | API Key | Use Case |
|----------|------|--------|---------|----------|
| Ollama | Local | mistral, llama2, mixtral, codellama | No | Development, Privacy |
| OpenAI | Cloud | gpt-4, gpt-4-turbo, gpt-3.5-turbo | Yes | Production, Advanced |

**Total: 2 providers with 7+ models supported! 🚀** 