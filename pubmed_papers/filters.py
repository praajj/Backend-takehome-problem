"""
Filtering logic to identify papers with authors from pharmaceutical/biotech companies.
"""
import logging
import re
from typing import List, Set

from pubmed_papers.models import Paper

# Configure logging
logger = logging.getLogger(__name__)

# Keywords that suggest academic affiliation
ACADEMIC_KEYWORDS = {
    'university', 'college', 'institute', 'school', 'academy', 'academia',
    'faculty', 'department', 'dept', 'laboratory', 'research center',
    'hospital', 'clinic', 'medical center', 'health center'
}

# Keywords that suggest pharmaceutical/biotech company affiliation
PHARMA_BIOTECH_KEYWORDS = {
    'pharma', 'biotech', 'therapeutics', 'bioscience', 'biopharm',
    'laboratories', 'labs', 'inc', 'llc', 'ltd', 'gmbh', 'corp', 'co.', 'plc',
    'biopharma', 'genomics', 'biologics', 'biotechnology'
}

# Common pharmaceutical/biotech company names for more accurate detection
COMMON_PHARMA_BIOTECH_COMPANIES = {
    'pfizer', 'merck', 'novartis', 'roche', 'johnson & johnson', 'j&j', 'jnj',
    'sanofi', 'glaxosmithkline', 'gsk', 'astrazeneca', 'gilead', 'amgen',
    'abbvie', 'lilly', 'eli lilly', 'bristol-myers squibb', 'bms', 'boehringer',
    'moderna', 'biogen', 'regeneron', 'bayer', 'vertex', 'novo nordisk',
    'takeda', 'astellas', 'daiichi sankyo', 'eisai', 'genentech', 'celgene',
    'alexion', 'incyte', 'biomarin', 'alkermes', 'ionis', 'illumina', '10x genomics'
}

# Email domains that suggest non-academic affiliation
NON_ACADEMIC_EMAIL_DOMAINS = {
    '.com', '.co', '.io', '.ai', '.bio', '.net'
}

# Email domains that suggest academic affiliation
ACADEMIC_EMAIL_DOMAINS = {
    '.edu', '.ac.', '.gov'
}


def identify_non_academic_authors(papers: List[Paper]) -> List[Paper]:
    """
    Identify authors with pharmaceutical/biotech company affiliations.
    
    Args:
        papers: List of Paper objects to analyze
    
    Returns:
        List of Paper objects with is_non_academic and company_affiliations populated
    """
    logger.debug(f"Identifying non-academic authors in {len(papers)} papers")
    
    for paper in papers:
        for author in paper.authors:
            author.is_non_academic = False
            author.company_affiliations = []
            
            # Check affiliations for company indicators
            for affiliation in author.affiliations:
                affiliation_lower = affiliation.lower()
                
                # Skip analysis if no real content
                if len(affiliation_lower) < 3:
                    continue
                
                # Check if contains known company names
                company_name = _extract_company_name(affiliation_lower)
                if company_name:
                    author.is_non_academic = True
                    author.company_affiliations.append(company_name)
                    continue
                
                # Check if contains pharma/biotech keywords but not academic keywords
                has_pharma_keyword = any(keyword in affiliation_lower for keyword in PHARMA_BIOTECH_KEYWORDS)
                has_academic_keyword = any(keyword in affiliation_lower for keyword in ACADEMIC_KEYWORDS)
                
                if has_pharma_keyword and not has_academic_keyword:
                    author.is_non_academic = True
                    author.company_affiliations.append(affiliation)
            
            # Check email domain as another signal
            if author.email:
                email_lower = author.email.lower()
                
                # Non-academic domains are stronger signals than academic ones
                has_non_academic_domain = any(domain in email_lower for domain in NON_ACADEMIC_EMAIL_DOMAINS)
                has_academic_domain = any(domain in email_lower for domain in ACADEMIC_EMAIL_DOMAINS)
                
                if has_non_academic_domain and not has_academic_domain and not author.is_non_academic:
                    author.is_non_academic = True
                    if not author.company_affiliations and author.affiliations:
                        author.company_affiliations = [author.affiliations[0]]
    
    # Filter out papers with no non-academic authors
    result = [paper for paper in papers if paper.has_non_academic_authors]
    logger.debug(f"Found {len(result)} papers with non-academic authors")
    
    return result


def _extract_company_name(affiliation: str) -> str:
    """
    Extract company name from affiliation string.
    
    Args:
        affiliation: Affiliation string to analyze
    
    Returns:
        Extracted company name or empty string if none found
    """
    # Check for known company names
    for company in COMMON_PHARMA_BIOTECH_COMPANIES:
        if company in affiliation:
            # Try to extract full company name with nearby words
            company_pattern = re.compile(r'(\w+\s+)?' + re.escape(company) + r'(\s+\w+)?', re.IGNORECASE)
            match = company_pattern.search(affiliation)
            if match:
                return match.group(0).strip()
            return company.title()
    
    # Look for company indicators like "Ltd", "Inc", etc.
    company_suffix_pattern = re.compile(r'([A-Z][A-Za-z0-9\-\s]+)\s+(?:Inc\.|Inc|Ltd\.|Ltd|LLC|GmbH|Corp\.|Corp|S\.A\.|PLC|Co\.|Co|Limited)', re.IGNORECASE)
    match = company_suffix_pattern.search(affiliation)
    if match:
        return match.group(0).strip()
    
    return ""


def filter_papers_with_company_affiliations(papers: List[Paper]) -> List[Paper]:
    """
    Filter papers to include only those with pharmaceutical/biotech company affiliations.
    
    Args:
        papers: List of Paper objects to filter
    
    Returns:
        List of Paper objects with non-academic authors
    """
    logger.debug(f"Filtering {len(papers)} papers for company affiliations")
    
    # First identify non-academic authors
    identified_papers = identify_non_academic_authors(papers)
    
    # Then filter for papers with at least one non-academic author
    result = [paper for paper in identified_papers if paper.has_non_academic_authors]
    
    logger.debug(f"Found {len(result)} papers with company affiliations")
    return result
