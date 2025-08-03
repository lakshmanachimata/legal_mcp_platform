import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { 
  FileText, 
  Search, 
  Download, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Building2,
  User,
  DollarSign,
  Calendar
} from 'lucide-react';

function App() {
  const [caseId, setCaseId] = useState('2024-PI-001');
  const [isLoading, setIsLoading] = useState(false);
  const [letterContent, setLetterContent] = useState('');
  const [caseData, setCaseData] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [allCasesData, setAllCasesData] = useState(null);
  const [isLoadingCases, setIsLoadingCases] = useState(false);
  
  // Fetch all cases data on component mount
  const fetchAllCasesData = async () => {
    setIsLoadingCases(true);
    try {
      const response = await axios.post('http://localhost:8000/rag/query', {
        query: "overall cases details",
        case_id: "system",
        context: {}
      });
      setAllCasesData(response.data);
    } catch (err) {
      console.error('Failed to fetch all cases data:', err);
    } finally {
      setIsLoadingCases(false);
    }
  };

  useEffect(() => {
    fetchAllCasesData();
  }, []);
  
  // Available cases for testing
  const availableCases = [
    { id: '2024-PI-001', name: '2024-PI-001 - Personal Injury (Motor Vehicle)' },
    { id: '2024-PI-002', name: '2024-PI-002 - Medical Malpractice' },
    { id: '2024-PI-003', name: '2024-PI-003 - Slip and Fall' }
  ];

  const generateLetter = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`http://localhost:8000/mcp/generate_demand_letter?case_id=${caseId}&template_type=demand_letter`, {
        additional_context: {}
      });
      
      setLetterContent(response.data.letter_content);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate letter');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCaseData = async () => {
    try {
      const response = await axios.post('http://localhost:8000/mcp/query', {
        method: 'legal.get_case_context',
        params: { case_id: caseId }
      });
      
      setCaseData(response.data.result);
    } catch (err) {
      console.error('Failed to fetch case data:', err);
    }
  };

  useEffect(() => {
    fetchCaseData();
  }, [caseId]);

  const downloadLetter = async () => {
    try {
      const response = await axios.post('http://localhost:8000/generate-pdf-json', {
        letter_content: letterContent,
        case_id: caseId
      }, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `demand_letter_${caseId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download PDF:', error);
      // Fallback to text download if PDF fails
      const element = document.createElement('a');
      const file = new Blob([letterContent], { type: 'text/plain' });
      element.href = URL.createObjectURL(file);
      element.download = `demand_letter_${caseId}.txt`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  };

  const CaseInfo = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-legal-800 mb-4 flex items-center">
        <Building2 className="w-5 h-5 mr-2" />
        Case Information
      </h3>
      
      {caseData ? (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-legal-50 p-4 rounded-lg">
              <h4 className="font-medium text-legal-700 mb-2">Case Details</h4>
              <p><span className="font-medium">ID:</span> {caseData.case.case_id}</p>
              <p><span className="font-medium">Type:</span> {caseData.case.case_type}</p>
              <p><span className="font-medium">Status:</span> {caseData.case.status}</p>
              <p><span className="font-medium">Summary:</span> {caseData.case.case_summary}</p>
            </div>
            
            <div className="bg-legal-50 p-4 rounded-lg">
              <h4 className="font-medium text-legal-700 mb-2 flex items-center">
                <User className="w-4 h-4 mr-1" />
                Parties
              </h4>
              {caseData.parties.map((party, index) => (
                <div key={index} className="mb-2">
                  <span className="font-medium capitalize">{party.party_type}:</span> {party.name}
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-legal-50 p-4 rounded-lg">
            <h4 className="font-medium text-legal-700 mb-2 flex items-center">
              <DollarSign className="w-4 h-4 mr-1" />
              Financial Summary
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(caseData.financials.reduce((acc, financial) => {
                const type = financial.record_type;
                if (!acc[type]) acc[type] = 0;
                acc[type] += financial.amount;
                return acc;
              }, {})).map(([type, amount]) => (
                <div key={type} className="text-center">
                  <div className="text-2xl font-bold text-primary-600">
                    ${amount.toLocaleString()}
                  </div>
                  <div className="text-sm text-legal-600 capitalize">{type.replace('_', ' ')}</div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-legal-50 p-4 rounded-lg">
            <h4 className="font-medium text-legal-700 mb-2 flex items-center">
              <Calendar className="w-4 h-4 mr-1" />
              Timeline Events
            </h4>
            <div className="space-y-2">
              {caseData.events.map((event, index) => (
                <div key={index} className="flex items-start">
                  <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                  <div>
                    <div className="font-medium">{event.event_date}</div>
                    <div className="text-legal-600">{event.description}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-legal-400" />
          <p className="text-legal-600">Loading case data...</p>
        </div>
      )}
    </div>
  );

  const LetterGenerator = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-legal-800 mb-4 flex items-center">
        <FileText className="w-5 h-5 mr-2" />
        Demand Letter Generator
      </h3>
      
      <div className="mb-6 p-4 bg-legal-50 border border-legal-200 rounded-md">
        <div className="flex items-center">
          <Building2 className="w-5 h-5 text-legal-600 mr-2" />
          <div>
            <div className="font-medium text-legal-800">Current Case: {caseId}</div>
            <div className="text-sm text-legal-600">{caseData?.case?.case_type} - {caseData?.case?.status}</div>
          </div>
        </div>
      </div>
      
      <button
        onClick={generateLetter}
        disabled={isLoading}
        className="w-full bg-primary-600 text-white py-3 px-4 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            Generating Letter...
          </>
        ) : (
          <>
            <FileText className="w-5 h-5 mr-2" />
            Generate Demand Letter for {caseId}
          </>
        )}
      </button>
      
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}
      
      {letterContent && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-medium text-legal-800">Generated Letter</h4>
            <button
              onClick={downloadLetter}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center"
            >
              <Download className="w-4 h-4 mr-2" />
              Download PDF
            </button>
          </div>
          
          <div className="bg-legal-50 border border-legal-200 rounded-md p-6">
            <div className="prose prose-legal max-w-none">
              <pre className="whitespace-pre-wrap font-mono text-sm text-legal-800">
                {letterContent}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const RAGQuery = () => {
    const [query, setQuery] = useState('');
    const [ragResponse, setRagResponse] = useState('');
    const [isQuerying, setIsQuerying] = useState(false);

    const submitQuery = async () => {
      if (!query.trim()) return;
      
      setIsQuerying(true);
      try {
        // Extract case_id from query if it contains a case reference
        let queryCaseId = caseId;
        const caseMatch = query.match(/case\s+([A-Z0-9-]+)/i);
        if (caseMatch) {
          queryCaseId = caseMatch[1];
        }
        
        const response = await axios.post('http://localhost:8000/rag/query', {
          query: query,
          case_id: queryCaseId,
          context: {}
        });
        
        setRagResponse(response.data.answer);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to query RAG');
      } finally {
        setIsQuerying(false);
      }
    };

    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-legal-800 mb-4 flex items-center">
          <Search className="w-5 h-5 mr-2" />
          RAG Query Interface
        </h3>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-legal-700 mb-2">
            Query
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-3 py-2 border border-legal-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Ask a question about the case..."
            rows={3}
          />
        </div>
        
        <button
          onClick={submitQuery}
          disabled={isQuerying || !query.trim()}
          className="w-full bg-primary-600 text-white py-3 px-4 rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {isQuerying ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Querying...
            </>
          ) : (
            <>
              <Search className="w-5 h-5 mr-2" />
              Submit Query
            </>
          )}
        </button>
        
        {ragResponse && (
          <div className="mt-6">
            <h4 className="text-lg font-medium text-legal-800 mb-4">Response</h4>
            <div className="bg-legal-50 border border-legal-200 rounded-md p-6">
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <span className="text-sm font-medium text-blue-800">
                  Querying case: {(() => {
                    const caseMatch = query.match(/case\s+([A-Z0-9-]+)/i);
                    return caseMatch ? caseMatch[1] : caseId;
                  })()}
                </span>
              </div>
              <div className="prose prose-legal max-w-none">
                <ReactMarkdown>{ragResponse}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-legal-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-legal-900 mb-2">
            Legal AI Case Management
          </h1>
          <p className="text-legal-600 text-lg">
            MCP + RAG Powered Demand Letter Generation
          </p>
        </header>

        {/* Case Selector */}
        <div className="mb-6 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-legal-800 mb-4 flex items-center">
            <Building2 className="w-5 h-5 mr-2" />
            Select Case
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {availableCases.map((caseOption) => (
              <button
                key={caseOption.id}
                onClick={() => setCaseId(caseOption.id)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  caseId === caseOption.id
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-legal-200 bg-white text-legal-700 hover:border-primary-300 hover:bg-primary-50'
                }`}
              >
                <div className="text-left">
                  <div className="font-medium">{caseOption.id}</div>
                  <div className="text-sm text-legal-600">{caseOption.name.split(' - ')[1]}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Case Info */}
          <div className="lg:col-span-1">
            <CaseInfo />
          </div>

          {/* Right Column - Main Interface */}
          <div className="lg:col-span-2">
            <div className="mb-6">
              <div className="flex space-x-1 bg-legal-200 p-1 rounded-lg">
                <button
                  onClick={() => setActiveTab('generate')}
                  disabled={!caseData}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'generate'
                      ? 'bg-white text-legal-900 shadow-sm'
                      : !caseData
                      ? 'text-legal-400 cursor-not-allowed'
                      : 'text-legal-600 hover:text-legal-900'
                  }`}
                >
                  <FileText className="w-4 h-4 mr-2 inline" />
                  Generate Letter
                  {!caseData && <span className="ml-1 text-xs">(No Case)</span>}
                </button>
                <button
                  onClick={() => setActiveTab('query')}
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'query'
                      ? 'bg-white text-legal-900 shadow-sm'
                      : 'text-legal-600 hover:text-legal-900'
                  }`}
                >
                  <Search className="w-4 h-4 mr-2 inline" />
                  RAG Query
                </button>
              </div>
            </div>

            {activeTab === 'generate' && caseData && <LetterGenerator />}
            {activeTab === 'generate' && !caseData && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="text-center py-8">
                  <AlertCircle className="w-12 h-12 text-legal-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-legal-700 mb-2">Case Not Found</h3>
                  <p className="text-legal-600">Please select a valid case to generate a demand letter.</p>
                </div>
              </div>
            )}
            {activeTab === 'query' && <RAGQuery />}
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-legal-500 text-sm">
          <p>
            Powered by Model Context Protocol (MCP) and Retrieval-Augmented Generation (RAG)
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App; 