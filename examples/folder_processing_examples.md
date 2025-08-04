# Folder Processing API Examples

This document provides examples of how to use the new folder processing API endpoints.

## API Endpoints

### 1. `/rag/process_folder` (FormData)
Process all PDF documents in a folder using form data.

### 2. `/rag/process_folder_json` (JSON)
Process all PDF documents in a folder using JSON request.

## Examples

### Using cURL with FormData

```bash
curl -X POST "http://localhost:8000/rag/process_folder" \
  -F "folder_path=challenge/sample_docs/2024-PI-001" \
  -F "case_id=2024-PI-001" \
  -F "provider=ollama" \
  -F "model=mistral" \
  -F "temperature=0.0"
```

### Using cURL with JSON

```bash
curl -X POST "http://localhost:8000/rag/process_folder_json" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "challenge/sample_docs/2024-PI-001",
    "case_id": "2024-PI-001",
    "provider": "ollama",
    "model": "mistral",
    "temperature": 0.0
  }'
```

### Using Python requests

```python
import requests

# JSON request
data = {
    'folder_path': 'challenge/sample_docs/2024-PI-001',
    'case_id': '2024-PI-001',
    'provider': 'ollama',
    'model': 'mistral',
    'temperature': 0.0
}

response = requests.post(
    'http://localhost:8000/rag/process_folder_json',
    json=data
)

result = response.json()
print(f"Processed {result['successful_processing']} files")
print(f"Total chunks: {result['summary']['total_chunks']}")
```

### Using JavaScript/Fetch

```javascript
const processFolder = async () => {
  const response = await fetch('http://localhost:8000/rag/process_folder_json', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      folder_path: 'challenge/sample_docs/2024-PI-001',
      case_id: '2024-PI-001',
      provider: 'ollama',
      model: 'mistral',
      temperature: 0.0
    })
  });
  
  const result = await response.json();
  console.log(`Processed ${result.successful_processing} files`);
  console.log(`Total chunks: ${result.summary.total_chunks}`);
};
```

## Response Format

The API returns a comprehensive response with processing results:

```json
{
  "case_id": "2024-PI-001",
  "folder_path": "challenge/sample_docs/2024-PI-001",
  "total_files": 4,
  "successful_processing": 4,
  "failed_processing": 0,
  "results": [
    {
      "file_name": "medical_records_dr_jones.pdf",
      "file_path": "challenge/sample_docs/2024-PI-001/medical_records_dr_jones.pdf",
      "document_id": "doc_123",
      "case_id": "2024-PI-001",
      "metadata": {
        "document_type": "medical_records",
        "parties": ["Dr. Jones", "John Smith"],
        "dates": ["2024-01-15"],
        "amounts": [5000]
      },
      "chunks_count": 8,
      "processing_status": "completed",
      "llm_provider": "ollama",
      "llm_model": "mistral"
    }
  ],
  "errors": [],
  "summary": {
    "total_chunks": 43,
    "llm_provider": "ollama",
    "llm_model": "mistral",
    "processing_completed": true
  }
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `folder_path` | string | Yes | Path to folder containing PDF documents |
| `case_id` | string | Yes | Case ID to associate documents with |
| `provider` | string | No | LLM provider (ollama/openai) |
| `model` | string | No | Model name for LLM provider |
| `base_url` | string | No | Base URL for Ollama |
| `api_key` | string | No | API key for OpenAI |
| `temperature` | float | No | Temperature for LLM generation |

## Error Handling

The API provides detailed error information:

```json
{
  "detail": "Folder path does not exist: /invalid/path"
}
```

Common error scenarios:
- Folder path doesn't exist
- Path is not a directory
- No PDF files found in folder
- Invalid case ID
- LLM provider configuration errors

## Benefits

1. **Batch Processing**: Process multiple documents at once
2. **Error Resilience**: Continues processing even if some files fail
3. **Detailed Reporting**: Comprehensive results and error reporting
4. **Flexible Configuration**: Support for different LLM providers
5. **Progress Tracking**: Individual file processing status

## Use Cases

- **Case Setup**: Process all documents for a new case
- **Document Updates**: Reprocess all documents when new files are added
- **Bulk Import**: Import documents from external systems
- **Testing**: Process test documents for validation 