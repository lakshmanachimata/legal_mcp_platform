# Legal AI Frontend

A React application that provides a user-friendly interface for the Legal AI Case Management System, demonstrating MCP and RAG technologies.

## Features

- **Case Information Display**: Shows case details, parties, financial summary, and timeline
- **Demand Letter Generation**: Generate demand letters using MCP and RAG
- **RAG Query Interface**: Interactive query interface for legal document analysis
- **Download Functionality**: Download generated letters as text files
- **Responsive Design**: Works on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Backend server running on `http://localhost:8000`

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view the app

## Usage

### Generate Demand Letter

1. Enter a case ID (default: `2024-PI-001`)
2. Click "Generate Demand Letter"
3. View the generated letter with RAG-sourced content
4. Download the letter as a text file

### RAG Query Interface

1. Switch to the "RAG Query" tab
2. Enter a natural language question about the case
3. Submit the query to get AI-powered responses
4. View responses with source attribution

## Technology Stack

- **React 18**: Modern React with hooks
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API calls
- **Lucide React**: Beautiful icons
- **React Markdown**: Markdown rendering

## API Integration

The frontend communicates with the backend API endpoints:

- `POST /mcp/generate_demand_letter` - Generate demand letters
- `POST /mcp/query` - Execute MCP queries
- `POST /rag/query` - Query RAG system

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

### Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── App.js          # Main application component
│   ├── index.js        # Application entry point
│   └── index.css       # Global styles with Tailwind
├── package.json
├── tailwind.config.js
└── postcss.config.js
```

## Features in Detail

### Case Information Panel

- **Case Details**: ID, type, status, summary
- **Parties**: Plaintiff and defendant information
- **Financial Summary**: Aggregated financial data by type
- **Timeline Events**: Chronological case events

### Letter Generation

- **Dynamic Content**: All content generated from database and RAG
- **Real-time Processing**: Shows loading states during generation
- **Error Handling**: Displays user-friendly error messages
- **Download**: Save letters as text files

### RAG Query Interface

- **Natural Language**: Ask questions in plain English
- **Context-Aware**: Responses based on case context
- **Source Attribution**: Shows where information comes from
- **Markdown Rendering**: Rich text formatting

## Styling

The app uses a custom color palette defined in `tailwind.config.js`:

- **Primary**: Blue tones for buttons and links
- **Legal**: Gray tones for text and backgrounds
- **Success**: Green for download buttons
- **Error**: Red for error messages

## Responsive Design

The app is fully responsive with:

- **Mobile-first**: Optimized for mobile devices
- **Tablet**: Side-by-side layout on medium screens
- **Desktop**: Full three-column layout on large screens

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest) 