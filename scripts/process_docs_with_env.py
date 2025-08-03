#!/usr/bin/env python3
"""
Script to process documents using LLM provider with API key from environment file
"""

import os
import sys
import asyncio
import requests
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config

def process_document_with_env(file_path: str, case_id: str, provider: str = "openai"):
    """Process a document using the LLM provider with API key from environment"""
    
    # Get API key from environment
    api_key = config.llm_config.api_key
    
    if not api_key:
        print(f"Error: No API key found for provider {provider}")
        return False
    
    # Prepare the request
    url = "http://127.0.0.1:8000/rag/process_document-with-provider"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'case_id': case_id,
            'provider': provider,
            'api_key': api_key,
            'model': config.llm_config.model,
            'temperature': config.llm_config.temperature
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Successfully processed {file_path}")
            print(f"   Document ID: {result.get('document_id')}")
            print(f"   Chunks: {result.get('chunks_count')}")
            print(f"   LLM Provider: {result.get('llm_provider')}")
            print(f"   LLM Model: {result.get('llm_model')}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error processing {file_path}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            return False

def main():
    """Main function to process all documents for case 2024-PI-001"""
    
    case_id = "2024-PI-001"
    docs_dir = Path("challenge/sample_docs/2024-PI-001")
    
    if not docs_dir.exists():
        print(f"❌ Directory {docs_dir} not found")
        return
    
    # Get all PDF files
    pdf_files = list(docs_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {docs_dir}")
        return
    
    print(f"📁 Processing {len(pdf_files)} documents for case {case_id}")
    print(f"🔧 Using LLM Provider: {config.llm_config.provider}")
    print(f"🤖 Using Model: {config.llm_config.model}")
    print(f"🔑 API Key: {'*' * 20 + config.llm_config.api_key[-10:] if config.llm_config.api_key else 'None'}")
    print()
    
    success_count = 0
    
    for pdf_file in pdf_files:
        print(f"📄 Processing: {pdf_file.name}")
        
        if process_document_with_env(str(pdf_file), case_id):
            success_count += 1
        print()
    
    print(f"📊 Summary: {success_count}/{len(pdf_files)} documents processed successfully")

if __name__ == "__main__":
    main() 