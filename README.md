# Research Article Assistant

A web application that helps users summarize and search scientific articles from ArXiv and HAL archives. It provides automatic summarization of scientific articles and keyword extraction to help users quickly understand research papers.

## Features

- **Article Summarization**: Generate concise summaries of scientific papers
- **Key Concept Extraction**: Identify the most important concepts in research papers
- **Research Search**: Search for articles on ArXiv and HAL archives
- **Clean User Interface**: Modern, responsive design for easy navigation

## Project Structure

The project is divided into two main components:

1. **Backend (Flask API)**: Handles article extraction, summarization, and search
2. **Frontend (React)**: Provides user interface for interacting with the API

## Technologies Used

### Backend

- Python 3.11+
- Flask (Web framework)
- LangChain (LLM integration)
- Groq (LLM provider)
- Pinecone (Vector database)

### Frontend

- React 19
- JavaScript/JSX
- CSS
- Vite (Build tool)

## Setup and Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- pnpm or npm
- Groq API Key
- Pinecone API Key and environment

### Backend Setup

1. Clone the repository

   ```bash
   git clone https://github.com/Hamza-cpp/research-assistant.git
   cd research-assistant
   ```

2. Create a Python virtual environment

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: venv\\Scripts\\activate
    ```

3. Install backend dependencies

   ```bash
   pip install -e .
   ```

4. Configure environment variables by creating a `.env` file in the root directory:

   ```bash
   # Flask settings
    FLASK_APP=main.py
    FLASK_DEBUG=True
    PORT=5000

    # API Keys
    GROQ_API_KEY=your_groq_api_key_here
    PINECONE_API_KEY=your_pinecone_api_key_here
    PINECONE_ENVIRONMENT=your_pinecone_environment_here
    ```

5. Run the backend server

   ```bash
   python main.py
   ```

   The API will be available at <http://localhost:5000>

### Frontend Setup

1. Navigate to the web-ui directory

   ```bash
   cd web-ui
   ```

2. Install frontend dependencies using pnpm

   ```bash
   pnpm install
   ```

   (Alternatively, you can use npm: `npm install`)

3. Start the development server

   ```bash
   pnpm run dev # or npm run dev
   ```

4. The frontend application will be available at <http://localhost:5173>

## API Endpoints

The backend provides the following API endpoints:

- `GET /api/health`: Health check endpoint
- `POST /api/summarize`: Summarize an article from its URL

    ```bash
    // Request Body
    {
    "article_url": "https://arxiv.org/abs/2303.08774"
    }
    ```

- `GET /api/search`: Search for articles

    ```bash
    // Query Parameters
    ?q=machine+learning&source=arxiv&max_results=10
    ```
