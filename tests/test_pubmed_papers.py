"""
Tests for the pubmed_papers package.
"""
import unittest
from datetime import date
from unittest.mock import patch

from pubmed_papers.filters import identify_non_academic_authors
from pubmed_papers.models import Author, Paper


class TestFilters(unittest.TestCase):
    """Tests for the filtering functionality."""
    
    def test_identify_non_academic_authors(self):
        """Test identifying non-academic authors."""
        # Create test papers with various author affiliations
        papers = [
            Paper(
                pubmed_id="1",
                title="Test Paper 1",
                publication_date=date(2023, 1, 1),
                authors=[
                    Author(
                        name="Academic Author",
                        affiliations=["University of Science, Department of Medicine"],
                        email="author@university.edu",
                    ),
                    Author(
                        name="Company Author",
                        affiliations=["Pfizer Inc., Research Division"],
                        email="author@pfizer.com",
                    ),
                ],
            ),
            Paper(
                pubmed_id="2",
                title="Test Paper 2",
                publication_date=date(2023, 2, 1),
                authors=[
                    Author(
                        name="Academic Author 2",
                        affiliations=["Medical School, Research Center"],
                        email="author2@med.edu",
                    ),
                ],
            ),
            Paper(
                pubmed_id="3",
                title="Test Paper 3",
                publication_date=date(2023, 3, 1),
                authors=[
                    Author(
                        name="Biotech Author",
                        affiliations=["GeneTech Biotech Company"],
                        email="author@genetech.com",
                    ),
                ],
            ),
        ]
        
        # Apply filter
        result = identify_non_academic_authors(papers)
        
        # Check results
        self.assertEqual(len(result), 3)  # All papers should be returned
        
        # Check author flags
        self.assertFalse(papers[0].authors[0].is_non_academic)  # Academic author
        self.assertTrue(papers[0].authors[1].is_non_academic)   # Pfizer author
        self.assertFalse(papers[1].authors[0].is_non_academic)  # Academic author
        self.assertTrue(papers[2].authors[0].is_non_academic)   # Biotech author
        
        # Check company affiliations
        self.assertEqual(len(papers[0].authors[1].company_affiliations), 1)
        self.assertEqual(len(papers[2].authors[0].company_affiliations), 1)
        
        # Check has_non_academic_authors property
        self.assertTrue(papers[0].has_non_academic_authors)
        self.assertFalse(papers[1].has_non_academic_authors)
        self.assertTrue(papers[2].has_non_academic_authors)


class TestModels(unittest.TestCase):
    """Tests for the data models."""
    
    def test_paper_properties(self):
        """Test Paper model properties."""
        # Create a test paper
        paper = Paper(
            pubmed_id="123",
            title="Test Paper",
            publication_date=date(2023, 1, 1),
            authors=[
                Author(
                    name="Academic Author",
                    affiliations=["University"],
                    email="academic@university.edu",
                    is_non_academic=False,
                ),
                Author(
                    name="Company Author",
                    affiliations=["Pfizer"],
                    email="company@pfizer.com",
                    is_non_academic=True,
                    company_affiliations=["Pfizer"],
                    is_corresponding_author=True,
                ),
            ],
        )
        
        # Test properties
        self.assertTrue(paper.has_non_academic_authors)
        self.assertEqual(len(paper.non_academic_authors), 1)
        self.assertEqual(paper.non_academic_authors[0].name, "Company Author")
        self.assertEqual(paper.corresponding_author_email, "company@pfizer.com")
        self.assertEqual(paper.company_affiliations, ["Pfizer"])


if __name__ == "__main__":
    unittest.main()