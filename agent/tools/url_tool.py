"""
URL Content Tool - Fetch and parse web page content.

Fetches URL content and converts HTML to markdown for documentation lookup.
"""
import re
from langchain_core.tools import StructuredTool
from typing import Optional, Dict


# Simple in-memory cache for URL content
_url_cache: Dict[str, str] = {}


def _html_to_markdown(html: str) -> str:
    """Simple HTML to text conversion. For full markdown, consider using html2text."""
    # Remove script and style elements
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert headers
    html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1\n', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert paragraphs and divs
    html = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<div[^>]*>(.*?)</div>', r'\1\n', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert lists
    html = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\1', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<ol[^>]*>(.*?)</ol>', r'\1', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert code blocks
    html = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'```\n\1\n```\n', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert links
    html = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Convert bold and italic
    html = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove remaining HTML tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Decode common HTML entities
    html = html.replace('&nbsp;', ' ')
    html = html.replace('&amp;', '&')
    html = html.replace('&lt;', '<')
    html = html.replace('&gt;', '>')
    html = html.replace('&quot;', '"')
    html = html.replace('&#39;', "'")
    
    # Clean up whitespace
    html = re.sub(r'\n{3,}', '\n\n', html)
    html = re.sub(r' +', ' ', html)
    
    return html.strip()


def _validate_url(url: str) -> tuple:
    """Validate and parse URL."""
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)
        
        if not parsed.netloc:
            return False, "Invalid URL: no domain specified", None
        
        if parsed.scheme not in ['http', 'https']:
            return False, f"Invalid URL scheme: {parsed.scheme}", None
        
        return True, None, url
        
    except Exception as e:
        return False, f"URL parsing error: {str(e)}", None


def get_url_content(url: str, use_cache: bool = True) -> str:
    """
    Fetch URL content and convert to markdown.
    """
    global _url_cache
    
    # Validate URL
    is_valid, error, normalized_url = _validate_url(url)
    if not is_valid:
        return error
    
    url = normalized_url
    
    # Check cache
    if use_cache and url in _url_cache:
        return _url_cache[url]
    
    try:
        # Try to import requests
        try:
            import requests
        except ImportError:
            return "Error: 'requests' package not installed. Run: pip install requests"
        
        # Fetch the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; SWE-AI Bot/1.0; +https://github.com/your-repo)'
        }
        
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        
        # Handle different content types
        if 'application/json' in content_type:
            import json
            try:
                data = response.json()
                content = f"```json\n{json.dumps(data, indent=2)}\n```"
            except:
                content = response.text
        elif 'text/plain' in content_type:
            content = response.text
        elif 'text/html' in content_type or not content_type:
            # Convert HTML to markdown
            content = _html_to_markdown(response.text)
        else:
            content = response.text
        
        # Truncate if too long
        max_length = 50000
        if len(content) > max_length:
            content = content[:max_length] + f"\n\n... (content truncated, {len(response.text)} total characters)"
        
        # Cache the result
        if use_cache:
            _url_cache[url] = content
        
        return content
        
    except Exception as e:
        error_type = type(e).__name__
        return f"Error fetching URL ({error_type}): {str(e)}"


def create_url_content_tool() -> StructuredTool:
    """Creates a URL content fetching tool."""
    
    def tool_get_url_content(url: str) -> str:
        """
        Fetch the content of a URL and return it in markdown format.
        
        Args:
            url: The URL to fetch (e.g., https://docs.example.com/api)
        
        Returns:
            Page content converted to markdown, or error message.
        """
        return get_url_content(url)
    
    return StructuredTool.from_function(
        func=tool_get_url_content,
        name="get_url_content",
        description=(
            "Fetch the full page content of a URL and return it in markdown format. "
            "Use this to read documentation, API references, Stack Overflow answers, "
            "or other web content. Results are cached to avoid repeated fetches."
        )
    )


def clear_url_cache():
    """Clear the URL content cache."""
    global _url_cache
    _url_cache = {}
