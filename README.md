# Scraping Real-estate Data with Scrapy and Playwright

A web scraping project that collects Belgian real estate data from Immovlan.be using Scrapy and Playwright integration (i.e., without API endpoints). The Scrapy Spider systematically scrapes house listings from the top 50 Belgian municipalities and exports cleaned data to CSV format.

This project scrapes real estate listings (houses and apartments for sale, excluding life annuity sale) from Immovlan.be for Belgium's 50 largest municipalities. It uses:
- **Scrapy** for web scraping framework
- **Playwright** for dynamic content rendering
- **Custom data cleaning pipeline** for standardized output
- **Dynamic CSV exporter** for flexible field handling

## 1. Key Features

- Scrapes 50+ municipalities with their suburbs
- Handles both static and JavaScript-rendered pages
- Intelligent duplicate detection
- Automatic data cleaning and normalization
- Real-time metrics and statistics display
- Concurrent requests for optimal performance

## 2. Installation

### 2.1. Prerequisites

- Python 3.12+
- pip package manager (or alternattively, conda package manager)  
  
Below, we provide some examples to set up the environment using `pip` package manager on a terminal.

### 2.2. Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd immo-eliza-scraping 
```
You can find the clone url in the `<Code>` green button. Make sure you clone this repository in the directory of your own choice.

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```
On Windows, you can run this command: `.venv\Scripts\activate`. Alternatively, if you use `conda` package manager, you can easily create a new virtual environment using `conda`. Please refer to their documentation on how to do this.

3. Install dependencies:
```bash
pip install -r requirements.txt
```  
This command will install:
- `scrapy` - Web scraping framework
- `scrapy-playwright` - Dynamic content rendering
- `pandas` - Data manipulation
If you use `conda`, please refer to `conda` documentation on how to install all the requirements.

4. Install Playwright browsers:
```bash
playwright install chromium
```

## 3. Usage

To run the Scrapy's spider to scrape all 50 municipalities based on the property type (houses or apartments), run the following script:

```python 
run_all_scrapers.py
```

### 3.1. Output Files

After scraping has been finalised, raw data files are stored in the `data` folder. Functions to clean the raw data can be found in `clean_data.py`, `combine_csv.py`, and `compare_columns.py`. 

Final output files are:
- **data/immo_all_properties.csv**: Main scraped data
- **log.txt**: Detailed scraping logs 
  
⚠️ Big data files! Github cannot render the output preview. ⚠️

## 4. Data Structure

### 4.1. Scraped Fields

Scrapy's spider extracts the following information for each property:

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

### 4.2. Data Cleaning

The pipeline automatically cleans:
- **Currency values**: "245 000 €" → `245000`
- **Surface areas**: "144 m²" → `144`
- **Energy values**: "629 kWh/m²/year" → `629`
- **Binary fields**: "Yes" → `1`, "No" → `0`
- **Missing data**: Various empty representations → `None`

## 5. Project Structure

```
immo-eliza-scraping/
├── data/                                          # Output directory
│   └── properties.csv          
├── immoeliza/                                     # Scrapy directory
│   ├── __init__.py                                # Initialization of scrapy
│   ├── items.py                                   # Dynamic item definition
│   ├── middlewares.py                             # Custom middlewares
│   ├── pipelines.py                               # Data cleaning pipeline
│   ├── settings.py                                # Scrapy settings
│   └── spiders
│       ├── __init__.py
│       ├── immovlan_apartments_by_municipality.py
│       └── immovlan_houses_by_municipality.py
├── .gitignore
├── clean_data.py
├── README.md                                      # This file
├── requirements.txt                               # Python dependencies
├── run_all_scrapers.py
└── scrapy.cfg                                     # Scrapy configuration 
```

## 6. Performance

### 6.1. Optimization Settings

- **Concurrent requests**: 60 total parallel scrapers, 30 per domain
- **Download delay**: 0.02 seconds
- **Resource filtering**: Blocks images, fonts, and media
- **Headless browser**: Chromium via Playwright (e.g., to handle cookies)

### 6.2. Typical Results

- **~10,000 properties** scraped across 50 municipalities
- **Processing time**: Varies by network speed and site response
- **Duplicate handling**: Automatic URL deduplication

### 6.3. Spider Workflow

1. Generate URLs for all municipality-page combinations
2. Parse listing pages to extract detail page links
3. Try static parsing first for speed
4. Fall back to Playwright rendering if needed
5. Extract structured data from detail pages
6. Clean and normalize data via pipeline
7. Export to CSV with dynamic fields

## 7. Authors

We are 🐠 Team Goldfish 🐠. This project is part of a teamwork at BeCode 2025 Arai 8. Please check the Contributors page for the link to each of our Github page or simply click on our names.

<div align="center">

🌊 [Intan K. Wardhani](https://github.com/intanwardhani) 🐠 [Jens Bogaert](https://github.com/BogJ674) 🐠 [Mohammed Amine Samoudi](https://github.com/AmineSam) 🐠 [Wiktor Porczyński](https://github.com/wikporc) 🌊

</div>

## 8. Acknowledgements

- Built with [Scrapy](https://scrapy.org/)
- Browser automation via [Playwright](https://playwright.dev/)
- Data from [Immovlan.be](https://www.immovlan.be/)
 
