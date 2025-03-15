"""
Command-line interface for the pubmed_papers module.

This file demonstrates how to separate the module functionality from the CLI,
as mentioned in the bonus task.
"""
import argparse
import sys

from pubmed_papers.module import get_papers, get_papers_dataframe, save_papers_to_csv


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


def main() -> None:
    """Main entry point for the command-line program using the module API."""
    # Parse command-line arguments
    args = parse_args()
    
    try:
        # Use the module API
        papers_df = get_papers_dataframe(args.query, args.max_results, args.debug)
        
        if papers_df.empty:
            print("No papers with pharmaceutical/biotech affiliations found")
            sys.exit(0)
        
        # Output results
        if args.file:
            # Save to file
            save_papers_to_csv(papers_df, args.file)
        else:
            # Print to stdout
            print(papers_df.to_csv(index=False))
        
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
