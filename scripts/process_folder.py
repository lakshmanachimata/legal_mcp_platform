#!/usr/bin/env python3
"""
Script to process all documents in a folder using the new folder processing API
"""

import os
import sys
import asyncio
import requests
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config

def process_folder_with_api(folder_path: str, case_id: str, provider: str = "ollama"):
    """Process all documents in a folder using the new API"""
    
    # Prepare the request
    url = "http://127.0.0.1:8000/rag/process_folder_json"
    
    data = {
        'folder_path': folder_path,
        'case_id': case_id,
        'provider': provider,
        'model': config.llm_config.model,
        'temperature': config.llm_config.temperature
    }
        
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Successfully processed folder: {folder_path}")
        print(f"   Case ID: {result.get('case_id')}")
        print(f"   Total Files: {result.get('total_files')}")
        print(f"   Successful: {result.get('successful_processing')}")
        print(f"   Failed: {result.get('failed_processing')}")
        print(f"   Total Chunks: {result.get('summary', {}).get('total_chunks', 0)}")
        print(f"   LLM Provider: {result.get('summary', {}).get('llm_provider')}")
        print(f"   LLM Model: {result.get('summary', {}).get('llm_model')}")
        
        # Print individual results
        if result.get('results'):
            print("\n📄 Processed Documents:")
            for doc in result['results']:
                print(f"   ✅ {doc['file_name']} - {doc['chunks_count']} chunks")
        
        if result.get('errors'):
            print("\n❌ Failed Documents:")
            for error in result['errors']:
                print(f"   ❌ {error['file_name']} - {error['error']}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error processing folder {folder_path}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

def main():
    """Main function to process documents for case 2024-PI-001"""
    
    case_id = "2024-PI-001"
    folder_path = "challenge/sample_docs/2024-PI-001"
    
    if not os.path.exists(folder_path):
        print(f"❌ Directory {folder_path} not found")
        return
    
    if not os.path.isdir(folder_path):
        print(f"❌ Path {folder_path} is not a directory")
        return
    
    # Check if there are PDF files
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ No PDF files found in {folder_path}")
        return
    
    print(f"📁 Processing folder: {folder_path}")
    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        print(f"   - {pdf_file}")
    print()
    print(f"🔧 Using LLM Provider: {config.llm_config.provider}")
    print(f"🤖 Using Model: {config.llm_config.model}")
    print()
    
    # Process the folder
    if process_folder_with_api(folder_path, case_id):
        print("\n🎉 Folder processing completed successfully!")
    else:
        print("\n💥 Folder processing failed!")

if __name__ == "__main__":
    main() 