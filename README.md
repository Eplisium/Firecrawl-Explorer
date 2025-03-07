# Firecrawl Explorer

![Firecrawl Explorer](https://img.shields.io/badge/Firecrawl-Explorer-orange)
![Python](https://img.shields.io/badge/Python-3.6+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A simple terminal UI for interacting with a self-hosted Firecrawl instance. This application provides a user-friendly interface to explore and utilize the various functionalities of a local Firecrawl instance, including web scraping, crawling, and data extraction.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Export System](#export-system)
- [API Client](#api-client)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

Firecrawl Explorer is a terminal-based application built with Python that provides an intuitive interface for interacting with a self-hosted Firecrawl instance. Firecrawl is an API service that takes a URL, crawls it, and converts it into clean markdown or structured data. It crawls all accessible subpages and gives you clean data for each.

The application uses the [Rich](https://github.com/Textualize/rich) library to create a visually appealing and interactive terminal UI, making it easy to use Firecrawl's powerful web scraping and crawling capabilities without having to write code or use complex API calls.

## Features

### 🔍 Scrape URL

Extract content from a single webpage in various formats:

- **Markdown**: Clean, readable text format
- **HTML**: Structured HTML content
- **Text**: Plain text content
- **JSON**: Structured data format

Options include:

- Extract only main content
- Include/exclude specific HTML tags
- Wait for JavaScript to load

### 🕸️ Crawl Website

Crawl an entire website and extract content from all pages:

- Follow links within the domain
- Process each page
- Return a structured dataset of all crawled pages

Options include:

- Include/exclude paths using regex patterns
- Set maximum crawl depth
- Limit number of pages to crawl
- Ignore sitemap
- Allow/disallow backward links
- Allow/disallow external links

### 🗺️ Map Website

Discover all links on a website:

- Search for specific terms
- Include/exclude subdomains
- Limit number of results
- Ignore sitemap or use sitemap only

### ⚙️ Settings

Configure your Firecrawl instance:

- API URL
- API Key (optional for self-hosted instances)
- Export directories

### 📁 Manage Exports

Browse and manage saved exports:

- View file contents
- Delete files
- Search for specific exports
- Open containing folder

### 📚 Help

Access documentation and information about the application:

- Keyboard shortcuts
- Feature descriptions
- Export system details

## Installation

### Prerequisites

- Python 3.6 or higher
- A self-hosted Firecrawl instance running locally or remotely

### Steps

1. Clone the repository or download the source code:

```bash
git clone https://github.com/yourusername/firecrawl-explorer.git
cd firecrawl-explorer
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

The requirements include:

- requests
- rich

3. Make the script executable (Linux/macOS):

```bash
chmod +x firecrawl_explorer.py
```

## Usage

### Starting the Application

Run the application using Python:

```bash
python firecrawl_explorer.py
```

Or directly (Linux/macOS):

```bash
./firecrawl_explorer.py
```

### Keyboard Shortcuts

- `1`: Go to Scrape URL
- `2`: Go to Crawl Website
- `3`: Go to Map Website
- `4`: Go to Settings
- `5`: Show Help
- `6`: Manage Exports
- `q`: Quit the application

### Scraping a URL

1. From the main menu, select option `1` (Scrape URL)
2. Enter the URL to scrape (default is <https://firecrawl.dev>)
3. Select the output format (markdown, HTML, text, or JSON)
4. Choose whether to extract only the main content
5. View the results in the terminal
6. Optionally save the results to a file

### Crawling a Website

1. From the main menu, select option `2` (Crawl Website)
2. Enter the URL to crawl (default is <https://firecrawl.dev>)
3. Configure crawl options:
   - Exclude paths (comma-separated)
   - Include paths (comma-separated)
   - Maximum depth
   - Maximum pages to crawl
4. Wait for the crawl to complete
5. View the results in the terminal
6. Optionally save the results to a file

### Mapping a Website

1. From the main menu, select option `3` (Map Website)
2. Enter the URL to map (default is <https://firecrawl.dev>)
3. Configure map options:
   - Search term (optional)
   - Include subdomains
   - Maximum links to return
4. View the results in the terminal
5. Optionally save the results to a file

### Managing Exports

1. From the main menu, select option `6` (Manage Exports)
2. Select a category to browse (Scrapes, Crawls, Maps, Docs, Custom, or All Exports)
3. View the list of files in the selected category
4. Choose an action:
   - View file contents
   - Open containing folder
   - Delete file
   - Search files

## Configuration

### API Settings

By default, Firecrawl Explorer connects to a local Firecrawl instance at `http://localhost:3002`. You can change this and other settings:

1. From the main menu, select option `4` (Settings)
2. Update the API URL if your Firecrawl instance is running at a different address
3. Add an API key if required (optional for self-hosted instances)
4. Configure export directories

### Export Directories

The application creates an `exports` directory in the same location as the script, with subdirectories for different types of exports:

- `exports/scrapes`: Single page scraping results
- `exports/crawls`: Multi-page crawling results
- `exports/maps`: Website mapping results
- `exports/docs`: Documentation and guides
- `exports/custom`: Any other exports

You can change these directories in the Settings menu.

## Export System

Firecrawl Explorer includes a comprehensive export system that allows you to save and organize your data:

### File Formats

- **Markdown (.md)**: Clean, readable text format
- **HTML (.html)**: Structured HTML content
- **Text (.txt)**: Plain text content
- **JSON (.json)**: Structured data format

### Metadata

You can add metadata to your exports:

- Descriptions
- Tags
- Export date and time
- Source URL

This metadata is stored either within the JSON file (for JSON exports) or in a separate `.meta.json` file (for other formats).

### Browsing Exports

The Manage Exports feature allows you to:

- Browse exports by category
- Search for specific exports
- View file contents
- Delete files
- Open containing folders

## API Client

The `FirecrawlClient` class provides a Python interface to the Firecrawl API:

### Methods

#### `scrape_url(url, params=None)`

Scrape a single URL.

Parameters:

- `url`: The URL to scrape
- `params`: Additional parameters for the scrape request
  - `formats`: List of formats to return (markdown, html, text, json)
  - `onlyMainContent`: Whether to only return the main content of the page
  - `includeTags`: List of HTML tags to include
  - `excludeTags`: List of HTML tags to exclude
  - `waitFor`: Time to wait for JavaScript to load in milliseconds

#### `crawl_url(url, params=None)`

Initiate a crawl job for the specified URL.

Parameters:

- `url`: The URL to crawl
- `params`: Additional parameters for the crawl request
  - `excludePaths`: List of URL pathname regex patterns to exclude
  - `includePaths`: List of URL pathname regex patterns to include
  - `maxDepth`: Maximum depth to crawl (default: 2)
  - `ignoreSitemap`: Whether to ignore the sitemap (default: false)
  - `limit`: Maximum number of pages to crawl (default: 10000)
  - `allowBackwardLinks`: Allow backward links (default: false)
  - `allowExternalLinks`: Allow external links (default: false)
  - `scrapeOptions`: Options for scraping each page

#### `check_crawl_status(crawl_id)`

Check the status of a crawl job.

Parameters:

- `crawl_id`: The ID of the crawl job

#### `map_url(url, params=None)`

Map a URL to discover all links.

Parameters:

- `url`: The URL to map
- `params`: Additional parameters for the map request
  - `search`: Search query to filter results
  - `ignoreSitemap`: Ignore the website sitemap (default: true)
  - `sitemapOnly`: Only return links from sitemap (default: false)
  - `includeSubdomains`: Include subdomains (default: false)
  - `limit`: Maximum number of links to return (default: 5000)
  - `timeout`: Timeout in milliseconds

#### `wait_for_crawl_completion(crawl_id, poll_interval=2, max_attempts=30)`

Wait for a crawl job to complete.

Parameters:

- `crawl_id`: The ID of the crawl job
- `poll_interval`: Time in seconds between status checks
- `max_attempts`: Maximum number of status check attempts

#### `save_to_file(data, directory, filename, format_type="text")`

Save data to a file.

Parameters:

- `data`: The data to save
- `directory`: The directory to save the file in
- `filename`: The name of the file
- `format_type`: The format of the data (markdown, html, text, json)

## Examples

### Example 1: Scraping a Blog Post

1. Start Firecrawl Explorer
2. Select option `1` (Scrape URL)
3. Enter the URL of a blog post
4. Select "markdown" as the output format
5. Choose "Yes" to extract only main content
6. View the clean, formatted content in the terminal
7. Save the results to a file

### Example 2: Crawling a Documentation Website

1. Start Firecrawl Explorer
2. Select option `2` (Crawl Website)
3. Enter the URL of a documentation website
4. Set exclude paths to avoid crawling irrelevant sections (e.g., `/blog/,/community/`)
5. Set maximum depth to 3
6. Set maximum pages to 200
7. Wait for the crawl to complete
8. Save the results to a file

### Example 3: Mapping a Website for Broken Links

1. Start Firecrawl Explorer
2. Select option `3` (Map Website)
3. Enter the website URL
4. Set a high limit to ensure all links are discovered
5. Save the results to a file
6. Use the data to check for broken links

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Firecrawl API
**Solution**:

- Ensure your Firecrawl instance is running
- Check the API URL in Settings
- Verify network connectivity
- Check if the API requires authentication

### Export Issues

**Problem**: Cannot save exports
**Solution**:

- Ensure you have write permissions to the export directories
- Check available disk space
- Try using a different export location

### Performance Issues

**Problem**: Crawling or mapping is slow
**Solution**:

- Reduce the maximum depth
- Reduce the maximum number of pages
- Use more specific include/exclude paths
- Check your network connection

## Contributing

Contributions to Firecrawl Explorer are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Submit a pull request

Please ensure your code follows the existing style and includes appropriate documentation.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Created with ❤️ for Firecrawl users
