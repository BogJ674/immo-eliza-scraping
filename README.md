# Immo Scraping with Scrapy

A web scraping project that collects Belgian real estate data from Immovlan using Scrapy with Playwright integration. The spider systematically scrapes house listings from the top 50 Belgian municipalities and exports cleaned data to CSV format.

## Project Description

This project scrapes real estate listings (houses for sale) from Immovlan.be for Belgium's 50 largest municipalities. It uses:
- **Scrapy** for web scraping framework
- **Playwright** for dynamic content rendering
- **Custom data cleaning pipeline** for standardized output
- **Dynamic CSV exporter** for flexible field handling

### Key Features

- Scrapes 50+ municipalities with their suburbs
- Handles both static and JavaScript-rendered pages
- Intelligent duplicate detection
- Automatic data cleaning and normalization
- **Beautiful Rich terminal interface** with real-time progress bars
- Real-time metrics and statistics display
- Concurrent requests for optimal performance

## Installation

### Prerequisites

- Python 3.14+ (or 3.8+)
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd immo-eliza-scraping
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

This will install:
- `scrapy` - Web scraping framework
- `scrapy-playwright` - Dynamic content rendering
- `pandas` - Data manipulation
- `rich` - Beautiful terminal output

4. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Basic Usage TODO: CHANGE TO REAL COMMANDS

Run the spider to scrape all 50 municipalities (default: 50 pages per municipality):
```bash
python run_all_scrapers.py
```

### Output Files TODO CHANGE TO REAL 

After running, you'll find:
- **data/immo_all_properties.csv** - Main scraped data
- **log.txt** - Detailed scraping logs

## Data Structure

### Scraped Fields

The spider extracts the following information for each property:

| Field | Description | Type |
|-------|-------------|------|
| `url` | Property listing URL | string |
| `property_id` | Unique property identifier | string |
| `municipality_url` | Municipality from URL | string |
| `price` | Property price | integer (€) |
| `number_of_bedrooms` | Number of bedrooms | integer |
| `number_of_bathrooms` | Number of bathrooms | integer |
| `number_of_facades` | Number of facades | integer |
| `garden` | Garden surface area | float (m²) |
| `terrace` | Terrace surface area | float (m²) |
| `furnished` | Is furnished | binary (0/1) |
| `garage` | Has garage | binary (0/1) |
| `elevator` | Has elevator | binary (0/1) |
| `specific_primary_energy_consumption` | Energy consumption | integer (kWh/m²/year) |
| `type_of_heating` | Heating system type | string |
| `flooding_area_type` | Flood risk info | string |
| ...and more | Various property details | mixed |

### Data Cleaning

The pipeline automatically cleans:
- **Currency values**: "245 000 €" → `245000`
- **Surface areas**: "144 m²" → `144`
- **Energy values**: "629 kWh/m²/year" → `629`
- **Binary fields**: "Yes" → `1`, "No" → `0`
- **Missing data**: Various empty representations → `None`

## Project Structure

```
immo-eliza-scraping/
├── immoeliza/
│   ├── spiders/
│   │   └── immovlan_houses_by_municipality.py  # Main spider
│   ├── items.py                                # Dynamic item definition
│   ├── pipelines.py                            # Data cleaning pipeline
│   ├── settings.py                             # Scrapy settings
│   └── middlewares.py                          # Custom middlewares
├── data/                                       # Output directory
│   ├── immo_houses_by_municipality.csv        # Scraped data
│   └── metrics_immo_houses_by_municipality.json # Statistics
├── scrapy.cfg                                  # Scrapy configuration
├── requirements.txt                            # Python dependencies
└── README.md                                   # This file
```

## Terminal Output

The scraper uses the [Rich](https://rich.readthedocs.io/) library to provide a beautiful terminal interface with:

- **Live progress bars** - Track municipalities and items being scraped in real-time
- **Formatted tables** - View final statistics in an organized table format
- **Colored output** - Easy-to-read color-coded logs and status messages
- **Time tracking** - See elapsed time and estimated time remaining

The Rich terminal extension automatically activates when you run the spider and provides:
- Opening banner with scraping configuration
- Real-time progress tracking for municipalities and items
- Final statistics table with comprehensive metrics
- Success/completion status panels

## Performance

### Optimization Settings

- **Concurrent requests**: 20 total, 16 per domain
- **Download delay**: 0.05 seconds
- **Resource filtering**: Blocks images, fonts, and media
- **Headless browser**: Chromium via Playwright

### Typical Results

- **~4,700 properties** scraped across 50 municipalities
- **Processing time**: Varies by network speed and site response
- **Duplicate handling**: Automatic URL deduplication

### Spider Workflow

1. Generate URLs for all municipality-page combinations
2. Parse listing pages to extract detail page links
3. Try static parsing first for speed
4. Fall back to Playwright rendering if needed
5. Extract structured data from detail pages
6. Clean and normalize data via pipeline
7. Export to CSV with dynamic fields

## Authors

- Jens Bogaert
- Mohammed Amine Samoudi
- Wiktor Porczyński
- Intan K. Wardhani

## Acknowledgments

- Built with [Scrapy](https://scrapy.org/)
- Browser automation via [Playwright](https://playwright.dev/)
- Data from [Immovlan.be](https://www.immovlan.be/)
Test for Pull request 
Test AMine branching 
Test test intan test  
