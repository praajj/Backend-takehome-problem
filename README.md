# PubMed Papers

A CLI tool to query PubMed for research papers authored by scientists affiliated with pharma and biotech industries.

## Features

- Advanced PubMed Search: Perform searches using full PubMed query syntax.
- Author Affiliation Detection: Automatically identify papers with at least one author affiliated with pharmaceutical or biotech companies.
- Detailed CSV Export: Export comprehensive results to a CSV file, including detailed information about papers and their authors.
- Flexible Command-Line Interface: User-friendly CLI with options for debugging and specifying custom output file paths.

## Code Organization

The project is organized as follows:

```
pubmed_papers/
├── pubmed_papers/
│   ├── __init__.py         # Package definition
│   ├── api.py              # PubMed API interaction
│   ├── filters.py          # Author affiliation filtering
│   ├── models.py           # Data models
│   ├── module.py           # Module API interface
│   ├── cli.py              # Command-line interface
│   └── cli_module.py       # Alternative CLI using the module API
├── tests/
│   ├── __init__.py
│   └── test_pubmed_papers.py  # Unit tests
├── pyproject.toml          # Poetry configuration
└── README.md               # Documentation
```

### Module Structure

- **api.py**: Contains functions for interacting with the PubMed API, including searching for papers and fetching detailed information.
- **filters.py**: Implements heuristics to identify non-academic authors and pharmaceutical/biotech company affiliations.
- **models.py**: Defines data classes for representing papers and authors.
- **module.py**: Provides a high-level API for using the package as a module.
- **cli.py**: Provides the command-line interface for the tool.
- **cli_module.py**: Alternative command-line interface that uses the module API.

## Installation

### Prerequisites

- Python 3.8 or higher
- [Poetry](https://python-poetry.org/) for dependency management

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/praajj/Backend-takehome-problem
   cd pubmed-papers
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

## Usage

### Basic Usage

```bash
get-papers-list "cancer therapy"
```

This will search PubMed for papers related to "cancer therapy", identify those with pharmaceutical/biotech company affiliations, and print the results to the console.

### Specifying Output File

```bash
get-papers-list "cancer therapy" --file results.csv
```

This will save the results to `results.csv` instead of printing to the console.

### Enabling Debug Mode

```bash
get-papers-list "cancer therapy" --debug
```

This will print detailed debug information during execution.

### Command-line Options

- `query`: PubMed search query (supports PubMed's full query syntax)
- `-d, --debug`: Print debug information during execution
- `-f, --file`: Specify the filename to save the results
- `-m, --max-results`: Maximum number of results to fetch (default: 1000)
- `-h, --help`: Display usage instructions

## Examples

### Search for Recent Cancer Therapy Papers

```bash
get-papers-list "cancer therapy AND 2022[pdat]" --file cancer_2022.csv
```

### Search for COVID-19 Vaccine Papers

```bash
get-papers-list "COVID-19 vaccine AND (clinical trial[pt])" --file covid_vaccines.csv
```

## Tools and Libraries Used

- [requests](https://requests.readthedocs.io/): HTTP library for making API calls
- [lxml](https://lxml.de/): XML parsing library
- [pandas](https://pandas.pydata.org/): Data manipulation library
- [tqdm](https://tqdm.github.io/): Progress bar library
- [Poetry](https://python-poetry.org/): Dependency management
- [mypy](http://mypy-lang.org/): Static type checking
- [black](https://black.readthedocs.io/): Code formatting
- [isort](https://pycqa.github.io/isort/): Import sorting

## Development

### Running Tests

```bash
poetry run pytest
```

### Type Checking

```bash
poetry run mypy pubmed_papers
```

### Code Formatting

```bash
poetry run black pubmed_papers
poetry run isort pubmed_papers
```

## Module API Usage

You can also use the package programmatically in your Python code:

```python
from pubmed_papers.module import get_papers, get_papers_dataframe, save_papers_to_csv

# Get papers as Python objects
papers = get_papers("cancer therapy", max_results=100)

# Or as a pandas DataFrame
papers_df = get_papers_dataframe("cancer therapy", max_results=100)

# Save to CSV
save_papers_to_csv(papers_df, "results.csv")
```

## TestPyPI Publishing

This package can be published to TestPyPI. See the [PUBLISHING.md](PUBLISHING.md) file for instructions.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
