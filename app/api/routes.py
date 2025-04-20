from flask import request, jsonify, current_app
from app.core.extractors.arxiv import ArxivExtractor
from app.core.extractors.hal import HalExtractor
from app.core.summarizer import LlamaSummarizer


# Initialize the summarizer
summarizer = None

def get_summarizer():
    global summarizer
    if summarizer is None:
        model = current_app.config.get("LLAMA_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        summarizer = LlamaSummarizer(model_name=model)
    return summarizer

def extract_article(url):
    """Extract article based on URL"""
    if 'arxiv.org' in url:
        return ArxivExtractor.extract_from_url(url)
    elif 'hal.archives-ouvertes.fr' in url or 'hal-' in url:
        return HalExtractor.extract_from_url(url)
    else:
        raise ValueError(f"Unsupported URL format: {url}")

def register_routes(app):
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """API health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'message': 'Research Article Summarization API is running'
        })

    @app.route('/api/summarize', methods=['POST'])
    def summarize():
        """Endpoint to summarize a research article"""
        try:
            data = request.json
            if not data or 'article_url' not in data:
                return jsonify({'error': 'Missing article_url in request body'}), 400
                
            article_url = data.get('article_url')
            
            # Extract article information
            article_data = extract_article(article_url)
            
            # Get the summarizer
            article_summarizer = get_summarizer()
            
            # Generate summary
            summary_result = article_summarizer.summarize(article_data)
            
            # Return the result
            return jsonify({
                'status': 'success',
                'article': {
                    'id': article_data.get('id'),
                    'title': article_data.get('title'),
                    'authors': article_data.get('authors', []),
                    'source': article_data.get('source'),
                    'url': article_url
                },
                'summary': summary_result.get('summary', ''),
                'key_concepts': summary_result.get('key_concepts', [])
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/search', methods=['GET'])
    def search():
        """Endpoint to search for articles"""
        try:
            query = request.args.get('q', '')
            source = request.args.get('source', 'arxiv')
            max_results = int(request.args.get('max_results', 10))
            
            if not query:
                return jsonify({'error': 'Missing query parameter'}), 400
                
            # Search based on source
            if source == 'arxiv':
                results = ArxivExtractor.search(query, max_results=max_results)
            elif source == 'hal':
                results = HalExtractor.search(query, max_results=max_results)
            else:
                return jsonify({'error': f'Unsupported source: {source}'}), 400
                
            return jsonify({
                'status': 'success',
                'query': query,
                'source': source,
                'results': results
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500