"""
Data models for PubMed papers and authors.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class Author:
    """Represents a paper author with their affiliation and contact information."""
    
    name: str
    affiliations: List[str] = field(default_factory=list)
    email: Optional[str] = None
    is_corresponding_author: bool = False
    is_non_academic: bool = False
    company_affiliations: List[str] = field(default_factory=list)


@dataclass
class Paper:
    """Represents a research paper with its metadata and authors."""
    
    pubmed_id: str
    title: str
    publication_date: date
    authors: List[Author] = field(default_factory=list)
    
    @property
    def non_academic_authors(self) -> List[Author]:
        """Return a list of authors affiliated with non-academic institutions."""
        return [author for author in self.authors if author.is_non_academic]
    
    @property
    def has_non_academic_authors(self) -> bool:
        """Check if the paper has at least one non-academic author."""
        return any(author.is_non_academic for author in self.authors)
    
    @property
    def corresponding_author_email(self) -> Optional[str]:
        """Return the email of the corresponding author, if available."""
        for author in self.authors:
            if author.is_corresponding_author and author.email:
                return author.email
        return None
    
    @property
    def company_affiliations(self) -> List[str]:
        """Return a list of unique company affiliations across all authors."""
        affiliations = []
        for author in self.non_academic_authors:
            affiliations.extend(author.company_affiliations)
        return list(set(affiliations))
