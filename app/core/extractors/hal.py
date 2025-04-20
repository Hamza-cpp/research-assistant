import requests
import re

class HalExtractor:
    """Class to extract articles from HAL archives"""
    
    BASE_API_URL = "https://api.archives-ouvertes.fr/search/"
    
    @staticmethod
    def extract_from_url(url):
        """Extract article content from a HAL URL"""
        # Extract the document ID from the URL
        match = re.search(r'hal-(\d+)', url)
        if not match:
            raise ValueError(f"Could not extract HAL ID from URL: {url}")
        
        doc_id = match.group(0)  # hal-XXXXXX format
        return HalExtractor.extract_by_id(doc_id)
    
    @staticmethod
    def extract_by_id(doc_id):
        """Extract article content using its HAL ID"""
        # Remove 'hal-' prefix if present
        if doc_id.startswith('hal-'):
            hal_id = doc_id
        else:
            hal_id = f"hal-{doc_id}"
        
        # Query the HAL API
        params = {
            'q': f'docid:{hal_id}',
            'fl': '*',
            'wt': 'json'
        }
        
        response = requests.get(HalExtractor.BASE_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data['response']['numFound'] == 0:
            raise ValueError(f"Article with ID {hal_id} not found")
        
        doc = data['response']['docs'][0]
        
        # Extract relevant fields
        title = doc.get('title_s', ['Unknown Title'])[0]
        abstract = doc.get('abstract_s', ['No abstract available'])[0]
        
        authors = []
        for auth_id in doc.get('authIdHalFullName_s', []):
            parts = auth_id.split('_FacetSep_')
            if len(parts) > 1:
                authors.append(parts[1])
        
        published_date = doc.get('publicationDateY_i', None)
        
        # Get PDF URL if available
        pdf_url = None
        if 'files_s' in doc:
            for file_info in doc['files_s']:
                if file_info.endswith('.pdf'):
                    pdf_url = file_info
                    break
        
        return {
            'id': hal_id,
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'published': published_date,
            'pdf_url': pdf_url,
            'source': 'hal'
        }
    
    @staticmethod
    def search(query, max_results=10):
        """Search for articles on HAL"""
        params = {
            'q': query,
            'rows': max_results,
            'sort': 'score desc',
            'fl': 'docid,title_s,abstract_s,uri_s',
            'wt': 'json'
        }
        
        response = requests.get(HalExtractor.BASE_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for doc in data['response']['docs']:
            title = doc.get('title_s', ['Unknown Title'])[0]
            abstract = doc.get('abstract_s', ['No abstract available'])[0] if 'abstract_s' in doc else "No abstract available"
            
            articles.append({
                'id': doc.get('docid'),
                'title': title,
                'abstract': abstract,
                'url': doc.get('uri_s'),
                'source': 'hal'
            })
        
        return articles