import re

def detect_source_from_url(url):
    """Detect the source of an article from its URL"""
    if 'arxiv.org' in url:
        return 'arxiv'
    elif 'hal.archives-ouvertes.fr' in url or 'hal-' in url:
        return 'hal'
    else:
        return None

def extract_arxiv_id(url):
    """Extract ArXiv ID from URL"""
    match = re.search(r'(\d+\.\d+|[a-z]+\/\d+)', url)
    if match:
        return match.group(0)
    return None

def extract_hal_id(url):
    """Extract HAL ID from URL"""
    match = re.search(r'hal-(\d+)', url)
    if match:
        return match.group(0)
    return None

def format_authors(authors_list):
    """Format a list of authors into a readable string"""
    if not authors_list:
        return ""
    
    if len(authors_list) == 1:
        return authors_list[0]
    elif len(authors_list) == 2:
        return f"{authors_list[0]} and {authors_list[1]}"
    else:
        return f"{authors_list[0]} et al."