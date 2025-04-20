import React, { useState } from "react";
import "./App.css";

const API_BASE_URL = "http://localhost:5000/api";

function App() {
  const [mode, setMode] = useState("summarize"); // 'summarize' or 'search'
  const [inputValue, setInputValue] = useState("");
  const [source, setSource] = useState("arxiv"); // For search: 'arxiv' or 'hal'
  const [results, setResults] = useState(null); // Will store the relevant part of the response
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (event) => {
    setInputValue(event.target.value);
  };

  const handleSourceChange = (event) => {
    setSource(event.target.value);
  };

  const handleModeChange = (event) => {
    setMode(event.target.value);
    setResults(null);
    setError(null);
    setInputValue("");
  };

  const handleSubmit = async (event) => {
    if (event && event.preventDefault) {
      event.preventDefault();
    }
    
    if (!inputValue.trim()) {
      setError(
        mode === "summarize"
          ? "Please enter an article URL."
          : "Please enter a search query."
      );
      return;
    }

    setIsLoading(true);
    setResults(null);
    setError(null);

    try {
      let response;
      let data; // Raw response data

      if (mode === "summarize") {
        // --- Summarize Mode ---
        response = await fetch(`${API_BASE_URL}/summarize`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ article_url: inputValue }),
        });

        data = await response.json(); // Parse the raw JSON response
        console.log("Summarize API response:", data); // Debug log

        if (!response.ok) {
          throw new Error(
            data.error || `Request failed with status ${response.status}`
          );
        }

        if (data.status === "success") {
          setResults({
            article: data.article,
            summary: data.summary,
            key_concepts: data.key_concepts,
          });
        } else {
          throw new Error(
            data.error || "An unknown error occurred during summarization."
          );
        }
      } else {
        // --- Search Mode ---
        const params = new URLSearchParams({
          q: inputValue,
          source: source,
          max_results: 10,
        });
        response = await fetch(`${API_BASE_URL}/search?${params.toString()}`);

        data = await response.json();
        console.log("Search API response:", data); // Debug log

        if (!response.ok) {
          throw new Error(
            data.error || `Request failed with status ${response.status}`
          );
        }

        if (data.status === "success") {
          setResults({
            query: data.query,
            source: data.source,
            results: data.results,
          });
        } else {
          throw new Error(
            data.error || "An unknown error occurred during search."
          );
        }
      }
    } catch (err) {
      console.error("API Error:", err);
      setError(
        err.message || "Failed to fetch data. Is the backend server running?"
      );
      setResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Render Helper Functions with improved UI ---
  const renderSummaryResults = () => {
    if (!results || !results.article || mode !== "summarize") return null;

    return (
      <div className="results-container">
        <h2>Summary Results</h2>
        <div className="results-card article-info">
          <div className="card-header">
            <h3>Article Details</h3>
          </div>
          <div className="card-content">
            <h4>{results.article?.title || "N/A"}</h4>
            <div className="meta-info">
              <span className="badge source-badge">
                {results.article?.source || "N/A"}
              </span>
              <span className="badge id-badge">
                {results.article?.id || "N/A"}
              </span>
            </div>
            <p className="authors">
              <i className="icon-users"></i>{" "}
              {(results.article?.authors || []).join(", ") || "N/A"}
            </p>
            <a
              href={results.article?.url}
              target="_blank"
              rel="noopener noreferrer"
              className="article-link"
            >
              <i className="icon-external-link"></i> View Original Article
            </a>
          </div>
        </div>

        <div className="results-card summary-content">
          <div className="card-header">
            <h3>Generated Summary</h3>
          </div>
          <div className="card-content">
            <p style={{ whiteSpace: "pre-wrap" }}>
              {results.summary || "No summary generated."}
            </p>
          </div>
        </div>

        <div className="results-card key-concepts">
          <div className="card-header">
            <h3>Key Concepts</h3>
          </div>
          <div className="card-content">
            {results.key_concepts && results.key_concepts.length > 0 ? (
              <div className="tags-container">
                {results.key_concepts.map((concept, index) => (
                  <span key={index} className="concept-tag">
                    {concept}
                  </span>
                ))}
              </div>
            ) : (
              <p>No key concepts extracted.</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderSearchResults = () => {
    if (!results || !results.results || mode !== "search") return null;

    return (
      <div className="results-container">
        <h2>Search Results</h2>
        <div className="search-info">
          <p>
            Found <span className="highlight">{results.results.length}</span>{" "}
            results for "<span className="highlight">{results.query}</span>"
            from <span className="highlight">{results.source}</span>
          </p>
        </div>

        {results.results && results.results.length > 0 ? (
          <div className="search-results-list">
            {results.results.map((item) => (
              <div key={item.id} className="search-result-card">
                <h3 className="result-title">{item.title || "No Title"}</h3>

                <div className="result-meta">
                  <span className="badge source-badge">
                    {item.source || results.source}
                  </span>
                  <span className="badge id-badge">{item.id}</span>
                </div>

                {item.authors && item.authors.length > 0 && (
                  <p className="authors">
                    <i className="icon-users"></i> {item.authors.join(", ")}
                  </p>
                )}

                {item.abstract && (
                  <p className="abstract">
                    {item.abstract.substring(0, 200)}...
                  </p>
                )}

                <div className="action-links">
                  {/* Consistent link display for both ArXiv and HAL */}
                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="view-button"
                    >
                      <i className="icon-external-link"></i> View on{" "}
                      {item.source === "hal" ? "HAL" : "ArXiv"}
                    </a>
                  )}

                  {/* Add summarize button for direct summarization */}
                  {item.url && (
                    <button
                      onClick={() => {
                        setMode("summarize");
                        setInputValue(item.url);
                        // Create a synthetic event and call handleSubmit
                        const syntheticEvent = { preventDefault: () => {} };
                        handleSubmit(syntheticEvent);
                      }}
                      className="summarize-button"
                    >
                      <i className="icon-file-text"></i> Summarize
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-results">
            <p>No results found. Try a different search term or source.</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Research Article Assistant</h1>
        <p className="subtitle">
          Summarize and search scientific articles from ArXiv and HAL
        </p>
      </header>

      <div className="content-container">
        <div className="control-panel">
          <div className="mode-selector">
            <button
              className={`mode-button ${mode === "summarize" ? "active" : ""}`}
              onClick={() =>
                handleModeChange({ target: { value: "summarize" } })
              }
            >
              <i className="icon-file-text"></i> Summarize
            </button>
            <button
              className={`mode-button ${mode === "search" ? "active" : ""}`}
              onClick={() => handleModeChange({ target: { value: "search" } })}
            >
              <i className="icon-search"></i> Search
            </button>
          </div>

          <form onSubmit={handleSubmit} className="input-form">
            {mode === "summarize" ? (
              <div className="input-group">
                <div className="input-with-icon">
                  <i className="icon-link"></i>
                  <input
                    type="url"
                    value={inputValue}
                    onChange={handleInputChange}
                    placeholder="Enter ArXiv or HAL article URL"
                    required
                    disabled={isLoading}
                    className="primary-input"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="primary-button"
                >
                  {isLoading ? "Processing..." : "Summarize"}
                </button>
              </div>
            ) : (
              <div className="input-group">
                <div className="input-with-icon">
                  <i className="icon-search"></i>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={handleInputChange}
                    placeholder="Enter search query (e.g., 'machine learning')"
                    required
                    disabled={isLoading}
                    className="primary-input"
                  />
                </div>
                <div className="source-toggle">
                  <button
                    type="button"
                    className={`source-button ${
                      source === "arxiv" ? "active" : ""
                    }`}
                    onClick={() => setSource("arxiv")}
                    disabled={isLoading}
                  >
                    ArXiv
                  </button>
                  <button
                    type="button"
                    className={`source-button ${
                      source === "hal" ? "active" : ""
                    }`}
                    onClick={() => setSource("hal")}
                    disabled={isLoading}
                  >
                    HAL
                  </button>
                </div>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="primary-button"
                >
                  {isLoading ? "Searching..." : "Search"}
                </button>
              </div>
            )}
          </form>
        </div>

        {isLoading && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Processing your request...</p>
          </div>
        )}

        {error && (
          <div className="error-container">
            <i className="icon-warning"></i>
            <p>{error}</p>
          </div>
        )}

        {/* Results section */}
        {mode === "summarize" ? renderSummaryResults() : renderSearchResults()}
      </div>

      <footer className="app-footer">
        <p>Research Article Assistant &copy; 2025</p>
      </footer>
    </div>
  );
}

export default App;