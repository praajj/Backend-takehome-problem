"""
Command-line interface for fetching PubMed papers with pharmaceutical/biotech affiliations.
"""
import argparse
import csv
import logging
import sys
from typing import List, Optional

from tqdm import tqdm

from pubmed_papers.api import fetch_papers_details, search_pubmed
from pubmed_papers.filters import filter_papers_with_company_affiliations
from pubmed_papers.models import Paper

# Configure logger
logger = logging.getLogger(__name__)


def setup_logging(debug: bool) -> None:
    """
    Configure logging based on debug flag.
    
    Args:
        debug: Whether to enable debug logging
    """
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Fetch research papers from PubMed with pharmaceutical/biotech affiliations."
    )
    
    parser.add_argument(
        "query",
        help="PubMed search query (supports PubMed's full query syntax)"
    )
    
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Print debug information during execution"
    )
    
    parser.add_argument(
        "-f", "--file",
        help="Specify the filename to save the results (CSV format)"
    )
    
    parser.add_argument(
        "-m", "--max-results",
        type=int,
        default=1000,
        help="Maximum number of results to fetch (default: 1000)"
    )
    
    return parser.parse_args()


def fetch_papers(query: str, max_results: int = 1000) -> List[Paper]:
    """
    Fetch papers matching the query and filter for pharmaceutical/biotech affiliations.
    
    Args:
        query: PubMed search query
        max_results: Maximum number of results to fetch
    
    Returns:
        List of Paper objects with pharmaceutical/biotech affiliations
    """
    # Search PubMed for matching papers
    logger.info(f"Searching PubMed for: {query}")
    pubmed_ids = search_pubmed(query, max_results)
    
    if not pubmed_ids:
        logger.info("No papers found matching the query")
        return []
    
    logger.info(f"Found {len(pubmed_ids)} papers matching the query")
    
    # Fetch paper details
    logger.info("Fetching paper details...")
    papers = fetch_papers_details(pubmed_ids)
    
    # Filter for papers with pharmaceutical/biotech company affiliations
    logger.info("Filtering for papers with pharmaceutical/biotech affiliations...")
    filtered_papers = filter_papers_with_company_affiliations(papers)
    
    logger.info(f"Found {len(filtered_papers)} papers with pharmaceutical/biotech affiliations")
    return filtered_papers


def write_to_csv(papers: List[Paper], filename: Optional[str] = None) -> None:
    """
    Write papers to CSV file or stdout.
    
    Args:
        papers: List of Paper objects to write
        filename: Output filename (if None, write to stdout)
    """
    # Define CSV columns
    fieldnames = [
        "PubmedID",
        "Title",
        "Publication Date",
        "Non-academic Author(s)",
        "Company Affiliation(s)",
        "Corresponding Author Email"
    ]
    
    # Prepare file or stdout
    if filename:
        output_file = open(filename, 'w', newline='', encoding='utf-8')
        logger.info(f"Writing results to {filename}")
    else:
        output_file = sys.stdout
        logger.info("Writing results to console")
    
    try:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        
        for paper in papers:
            # Prepare row data
            row = {
                "PubmedID": paper.pubmed_id,
                "Title": paper.title,
                "Publication Date": paper.publication_date.isoformat(),
                "Non-academic Author(s)": "; ".join(a.name for a in paper.non_academic_authors),
                "Company Affiliation(s)": "; ".join(paper.company_affiliations),
                "Corresponding Author Email": paper.corresponding_author_email or "",
            }
            
            writer.writerow(row)
    
    finally:
        if filename:
            output_file.close()


def main() -> None:
    """Main entry point for the command-line program."""
    # Parse command-line arguments
    args = parse_args()
    
    # Set up logging
    setup_logging(args.debug)
    
    try:
        # Fetch papers
        papers = fetch_papers(args.query, args.max_results)
        
        if not papers:
            logger.warning("No papers with pharmaceutical/biotech affiliations found")
            sys.exit(0)
        
        # Write results to CSV
        write_to_csv(papers, args.file)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            import traceback
            logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
