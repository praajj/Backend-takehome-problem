"""
Functions for interacting with the PubMed API.
"""
import logging
import time
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import quote_plus

import requests
from lxml import etree

from pubmed_papers.models import Author, Paper

# Configure logging
logger = logging.getLogger(__name__)

# API Constants
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_SEARCH_URL = f"{PUBMED_BASE_URL}/esearch.fcgi"
PUBMED_FETCH_URL = f"{PUBMED_BASE_URL}/efetch.fcgi"
PUBMED_SUMMARY_URL = f"{PUBMED_BASE_URL}/esummary.fcgi"
RESULTS_PER_PAGE = 100
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds


def search_pubmed(query: str, max_results: int = 1000) -> List[str]:
    """
    Search PubMed for papers matching the query.
    
    Args:
        query: The search query using PubMed's query syntax
        max_results: Maximum number of results to return
    
    Returns:
        List of PubMed IDs matching the search query
    
    Raises:
        requests.RequestException: If there is an error connecting to the PubMed API
    """
    logger.debug(f"Searching PubMed with query: {query}")
    pubmed_ids = []
    
    # Initial search to get total count and first batch of results
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": min(RESULTS_PER_PAGE, max_results),
        "usehistory": "y",
    }
    
    search_response = _make_request(PUBMED_SEARCH_URL, params)
    search_data = search_response.json()
    
    if "esearchresult" not in search_data:
        logger.warning("No search results found or invalid response format")
        return []
    
    result = search_data["esearchresult"]
    total_count = int(result.get("count", 0))
    logger.debug(f"Found {total_count} total results")
    
    # Add IDs from the first batch
    pubmed_ids.extend(result.get("idlist", []))
    
    # Get WebEnv and QueryKey for subsequent batches
    web_env = result.get("webenv")
    query_key = result.get("querykey")
    
    if web_env and query_key and total_count > RESULTS_PER_PAGE and len(pubmed_ids) < max_results:
        remaining = min(total_count, max_results) - len(pubmed_ids)
        
        # Fetch additional batches
        for start in range(RESULTS_PER_PAGE, min(total_count, max_results), RESULTS_PER_PAGE):
            batch_size = min(RESULTS_PER_PAGE, remaining)
            logger.debug(f"Fetching batch starting at {start}, size {batch_size}")
            
            params = {
                "db": "pubmed",
                "query_key": query_key,
                "WebEnv": web_env,
                "retstart": start,
                "retmax": batch_size,
                "retmode": "json",
            }
            
            batch_response = _make_request(PUBMED_SEARCH_URL, params)
            batch_data = batch_response.json()
            
            if "esearchresult" in batch_data and "idlist" in batch_data["esearchresult"]:
                new_ids = batch_data["esearchresult"]["idlist"]
                pubmed_ids.extend(new_ids)
                remaining -= len(new_ids)
            
            # Respect API rate limits
            time.sleep(0.34)  # PubMed allows ~3 requests per second
    
    logger.debug(f"Retrieved {len(pubmed_ids)} PubMed IDs")
    return pubmed_ids


def fetch_papers_details(pubmed_ids: List[str]) -> List[Paper]:
    """
    Fetch detailed information for the given PubMed IDs.
    
    Args:
        pubmed_ids: List of PubMed IDs to fetch
    
    Returns:
        List of Paper objects with detailed information
    """
    if not pubmed_ids:
        logger.warning("No PubMed IDs provided")
        return []
    
    logger.debug(f"Fetching details for {len(pubmed_ids)} papers")
    papers = []
    
    # Process in batches to avoid oversized requests
    batch_size = 100
    for i in range(0, len(pubmed_ids), batch_size):
        batch_ids = pubmed_ids[i:i+batch_size]
        logger.debug(f"Processing batch {i//batch_size + 1} with {len(batch_ids)} IDs")
        
        params = {
            "db": "pubmed",
            "id": ",".join(batch_ids),
            "retmode": "xml",
        }
        
        response = _make_request(PUBMED_FETCH_URL, params)
        
        # Parse XML response
        try:
            root = etree.fromstring(response.content)
            article_elements = root.xpath("//PubmedArticle")
            
            for article in article_elements:
                try:
                    paper = _parse_pubmed_article(article)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing article: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing XML response: {e}")
        
        # Respect API rate limits
        time.sleep(0.34)
    
    logger.debug(f"Successfully fetched details for {len(papers)} papers")
    return papers


def _make_request(url: str, params: Dict[str, str], 
                  retry_count: int = RETRY_COUNT) -> requests.Response:
    """
    Make an HTTP request with retry logic.
    
    Args:
        url: The URL to request
        params: Query parameters
        retry_count: Number of retry attempts
    
    Returns:
        Response object
    
    Raises:
        requests.RequestException: If all retry attempts fail
    """
    for attempt in range(retry_count):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt+1}/{retry_count}): {e}")
            if attempt < retry_count - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                logger.error(f"Request failed after {retry_count} attempts")
                raise


def _parse_pubmed_article(article_element: etree._Element) -> Optional[Paper]:
    """
    Parse a PubmedArticle XML element into a Paper object.
    
    Args:
        article_element: The XML element containing article data
    
    Returns:
        Paper object or None if parsing fails
    """
    try:
        # Extract PubMed ID
        pubmed_id_elem = article_element.xpath(".//PMID")
        if not pubmed_id_elem:
            return None
        pubmed_id = pubmed_id_elem[0].text
        
        # Extract article title
        title_elem = article_element.xpath(".//ArticleTitle")
        title = title_elem[0].text if title_elem else "No title available"
        
        # Extract publication date
        pub_date = _extract_publication_date(article_element)
        
        # Create Paper object
        paper = Paper(
            pubmed_id=pubmed_id,
            title=title,
            publication_date=pub_date,
            authors=[]
        )
        
        # Extract authors and affiliations
        author_list = article_element.xpath(".//AuthorList/Author")
        for author_elem in author_list:
            author = _parse_author(author_elem)
            if author:
                paper.authors.append(author)
        
        return paper
    except Exception as e:
        logger.error(f"Error parsing article with ID {article_element.xpath('.//PMID/text()')}: {e}")
        return None


def _parse_author(author_elem: etree._Element) -> Optional[Author]:
    """
    Parse an Author XML element into an Author object.
    
    Args:
        author_elem: The XML element containing author data
    
    Returns:
        Author object or None if parsing fails
    """
    try:
        # Extract author name
        last_name = author_elem.xpath("./LastName/text()")
        fore_name = author_elem.xpath("./ForeName/text()")
        
        if last_name and fore_name:
            name = f"{fore_name[0]} {last_name[0]}"
        elif last_name:
            name = last_name[0]
        else:
            collective_name = author_elem.xpath("./CollectiveName/text()")
            if collective_name:
                name = collective_name[0]
            else:
                return None
        
        # Extract affiliations
        affiliations = []
        affiliation_elems = author_elem.xpath("./AffiliationInfo/Affiliation")
        for aff_elem in affiliation_elems:
            if aff_elem.text:
                affiliations.append(aff_elem.text)
        
        # Extract email from affiliations
        email = None
        for affiliation in affiliations:
            email_match = [e for e in affiliation.split() if '@' in e and '.' in e]
            if email_match:
                email = email_match[0].strip('.,;<>')
                break
        
        # Check if corresponding author
        is_corresponding = bool(author_elem.xpath("./@CorrespAuthor") and 
                             author_elem.xpath("./@CorrespAuthor")[0] == "Y")
        
        author = Author(
            name=name,
            affiliations=affiliations,
            email=email,
            is_corresponding_author=is_corresponding,
        )
        
        return author
    except Exception as e:
        logger.error(f"Error parsing author: {e}")
        return None


def _extract_publication_date(article_element: etree._Element) -> date:
    """
    Extract publication date from article element.
    
    Args:
        article_element: The XML element containing article data
    
    Returns:
        Publication date as date object
    """
    try:
        # Try to get date from PubDate
        pub_date_elem = article_element.xpath(".//PubDate")
        if pub_date_elem:
            year_elem = pub_date_elem[0].xpath("./Year/text()")
            month_elem = pub_date_elem[0].xpath("./Month/text()")
            day_elem = pub_date_elem[0].xpath("./Day/text()")
            
            year = int(year_elem[0]) if year_elem else 1900
            
            # Handle text month names
            month = 1
            if month_elem:
                try:
                    month = int(month_elem[0])
                except ValueError:
                    # Try to parse month name
                    month_str = month_elem[0].lower()[:3]
                    month_map = {
                        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
                    }
                    month = month_map.get(month_str, 1)
            
            day = int(day_elem[0]) if day_elem else 1
            
            try:
                return date(year, month, day)
            except ValueError:
                # Handle invalid dates
                return date(year, 1, 1)
        
        # Fallback to current date
        return date.today()
    except Exception:
        return date.today()
