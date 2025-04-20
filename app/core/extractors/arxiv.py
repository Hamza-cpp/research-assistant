import requests
import xml.etree.ElementTree as ET
import re


class ArxivExtractor:
    """Class to extract articles from ArXiv API"""

    BASE_URL = "http://export.arxiv.org/api/query"

    @staticmethod
    def extract_from_url(url):
        """
        Extract article content from an ArXiv URL (abs or pdf page).
        Handles both new (YYMM.NNNNN) and old (archive/YYMMNNN) ID formats.
        """
        # Regex to find the ID after /abs/ or /pdf/
        # It captures the part after the slash until the end of the path,
        # or before a query parameter '?' or fragment '#'
        # Handles IDs with slashes (like hep-ex/12345) and version numbers (v1, v2)
        
        
        
        
        # match = re.search(r'/(?:abs|pdf)/([^/?#]+)', url)
                # Allow '/' within the ID, stop only at '?' or '#' or end of string
        match = re.search(r'/(?:abs|pdf)/([^?#]+)', url)

        if not match:
             raise ValueError(f"Could not extract ArXiv ID pattern (e.g., /abs/...) from URL: {url}")


        article_id = match.group(1)

        # If the extracted ID ends with .pdf, remove that extension
        if article_id.lower().endswith('.pdf'):
            article_id = article_id[:-4]

        # Basic validation: Ensure ID is not empty after potential .pdf removal
        if not article_id:
             raise ValueError(f"Extracted empty ArXiv ID from URL: {url}")

        print(f"Extracted ArXiv ID: {article_id}")  # Debug log remains useful

        # No need for the 'abs' or 'pdf' check here anymore if the regex matched
        # if article_id == 'abs' or article_id == 'pdf':
        #     raise ValueError(f"Invalid ArXiv ID extracted ('abs' or 'pdf'): {url}")

        return ArxivExtractor.extract_by_id(article_id)

    @staticmethod
    def extract_by_id(article_id):
        """Extract article content using its ArXiv ID"""
        print(f"Querying API with ID: {article_id}") # Add debug log
        params = {
            'id_list': article_id,
            'max_results': 1
        }

        try:
            response = requests.get(ArxivExtractor.BASE_URL, params=params)
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.RequestException as e:
             # Catch potential network errors or bad HTTP statuses
             print(f"Error during API request: {e}")
             # Re-raise or handle as appropriate for your application
             # Returning the original error might be helpful for debugging in the calling code
             raise ValueError(f"Error fetching data from ArXiv API for ID {article_id}: {e}") from e


        # Parse the XML response
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            print(f"Error parsing XML response: {e}")
            print(f"Response content: {response.text[:500]}...") # Log part of the response
            raise ValueError(f"Could not parse ArXiv API response for ID {article_id}") from e


        # Extract the article details
        # Define namespace map INSIDE the function or pass it if needed elsewhere
        namespace = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        entry = root.find('.//atom:entry', namespace)

        # Check for ArXiv API errors embedded in the feed
        if entry is not None and entry.find('./atom:title', namespace).text == 'Error':
             error_summary = entry.find('./atom:summary', namespace).text
             print(f"ArXiv API returned an error for ID {article_id}: {error_summary}")
             raise ValueError(f"ArXiv API error for ID {article_id}: {error_summary}")

        if entry is None:
            # Check if the root itself indicates zero results (though the API usually returns an error entry)
            opensearch_ns = {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}
            total_results_elem = root.find('.//opensearch:totalResults', {**namespace, **opensearch_ns})
            if total_results_elem is not None and total_results_elem.text == '0':
                 raise ValueError(f"Article with ID {article_id} not found (0 results)")
            else:
                 # General "not found" or unexpected response structure
                 print(f"Response content (entry not found): {response.text[:500]}...")
                 raise ValueError(f"Article with ID {article_id} not found or API response structure unexpected.")


        # Helper function to safely get text, handling None elements
        def get_text(element, path, ns):
            found = element.find(path, ns)
            return found.text.strip() if found is not None and found.text else ""

        title = get_text(entry, './atom:title', namespace)
        abstract = get_text(entry, './atom:summary', namespace)
        # Use a list comprehension with the helper for safety
        authors = [get_text(author, './atom:name', namespace) for author in entry.findall('./atom:author', namespace)]
        # Filter out empty author names if any occurred
        authors = [name for name in authors if name]
        published = get_text(entry, './atom:published', namespace)
        updated = get_text(entry, './atom:updated', namespace) # Good to have updated date too

        # Get PDF URL (more robustly)
        pdf_url = None
        # Also get the abstract page URL (useful)
        abs_url = None
        for link in entry.findall('./atom:link', namespace):
            link_title = link.get('title')
            link_rel = link.get('rel')
            link_href = link.get('href')
            if link_title == 'pdf' and link_rel == 'related':
                pdf_url = link_href
            elif link_rel == 'alternate' and link.get('type') == 'text/html':
                 abs_url = link_href # This is usually the link to the abstract page

        # Extract the ID *from the API response* as the canonical ID
        # This handles potential version updates if you didn't specify one
        canonical_id_url = get_text(entry, './atom:id', namespace)
        canonical_id = canonical_id_url.split('/abs/')[-1] if '/abs/' in canonical_id_url else article_id


        return {
            'id': canonical_id, # Use the ID confirmed by the API
            'title': title,
            'abstract': abstract,
            'authors': authors,
            'published': published,
            'updated': updated,
            'pdf_url': pdf_url,
            'abs_url': abs_url, # Add abstract page URL
            'source': 'arxiv'
        }

    @staticmethod
    def search(query, max_results=10):
        """Search for articles on ArXiv"""
        params = {
            'search_query': query,
            'max_results': max_results,
            'sortBy': 'relevance', # or 'lastUpdatedDate', 'submittedDate'
            'sortOrder': 'descending' # or 'ascending'
        }

        try:
            response = requests.get(ArxivExtractor.BASE_URL, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
             print(f"Error during API search request: {e}")
             raise ValueError(f"Error searching ArXiv API for query '{query}': {e}") from e

        # Parse the XML response
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            print(f"Error parsing XML search response: {e}")
            print(f"Response content: {response.text[:500]}...")
            raise ValueError(f"Could not parse ArXiv API search response for query '{query}'") from e

        # Extract the articles
        namespace = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}

        # Helper function to safely get text
        def get_text(element, path, ns):
            found = element.find(path, ns)
            return found.text.strip() if found is not None and found.text else ""

        entries = root.findall('.//atom:entry', namespace)
        articles = []
        for entry in entries:
             # Check if this entry is an error message
             if get_text(entry, './atom:title', namespace) == 'Error':
                 error_summary = get_text(entry, './atom:summary', namespace)
                 print(f"ArXiv API returned an error during search: {error_summary}")
                 # Decide whether to skip or raise an error - skipping might be okay in search
                 continue

             id_url = get_text(entry, './atom:id', namespace)
             # Extract ID robustly from the ID URL provided in the entry
             article_id = id_url.split('/abs/')[-1] if '/abs/' in id_url else None
             if not article_id:
                 print(f"Warning: Could not extract article ID from entry URL: {id_url}")
                 continue # Skip entries where ID extraction fails

             title = get_text(entry, './atom:title', namespace)
             abstract = get_text(entry, './atom:summary', namespace)
             authors = [get_text(author, './atom:name', namespace) for author in entry.findall('./atom:author', namespace)]
             authors = [name for name in authors if name] # Filter empty names
             published = get_text(entry, './atom:published', namespace)
             updated = get_text(entry, './atom:updated', namespace)

             # Find PDF/alternate links
             pdf_url, abs_url = None, None
             for link in entry.findall('./atom:link', namespace):
                 link_title = link.get('title')
                 link_rel = link.get('rel')
                 link_href = link.get('href')
                 if link_title == 'pdf' and link_rel == 'related':
                     pdf_url = link_href
                 elif link_rel == 'alternate' and link.get('type') == 'text/html':
                     abs_url = link_href

             articles.append({
                 'id': article_id,
                 'title': title,
                 'abstract': abstract,
                 'authors': authors, # Add authors to search results
                 'published': published, # Add dates
                 'updated': updated,
                 'pdf_url': pdf_url, # Add URLs if available
                 'abs_url': abs_url,
                 'source': 'arxiv'
             })

        return articles
