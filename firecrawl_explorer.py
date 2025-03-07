#!/usr/bin/env python3
"""
Firecrawl Explorer - A simple terminal UI for interacting with a self-hosted Firecrawl instance.

This script provides a user-friendly interface to explore and utilize the various functionalities
of a local Firecrawl instance, including web scraping, crawling, and data extraction.
"""

import os
import sys
import json
import time
import threading
import requests
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.live import Live
from rich import box
from rich.layout import Layout

# Configuration
DEFAULT_API_URL = "http://localhost:3002"
DEFAULT_TEST_URL = "https://firecrawl.dev"

class FirecrawlClient:
    """Client for interacting with the Firecrawl API."""
    
    def __init__(self, api_url: str = DEFAULT_API_URL, api_key: Optional[str] = None):
        """
        Initialize the Firecrawl client.
        
        Args:
            api_url: The URL of the Firecrawl API.
            api_key: Optional API key for authentication.
        """
        self.api_url = api_url
        self.api_key = api_key
        self.console = Console()
    
    def _prepare_headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        """Prepare headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if idempotency_key:
            headers["x-idempotency-key"] = idempotency_key
        return headers
    
    def scrape_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scrape a URL using the Firecrawl API.
        
        Args:
            url: The URL to scrape.
            params: Additional parameters for the scrape request.
                formats: List of formats to return (markdown, html, text, json, etc.)
                onlyMainContent: Whether to only return the main content of the page
                includeTags: List of HTML tags to include
                excludeTags: List of HTML tags to exclude
                waitFor: Time to wait for JavaScript to load in milliseconds
                
        Returns:
            The scrape response.
        """
        endpoint = "/v1/scrape"
        headers = self._prepare_headers()
        
        # Default parameters if none provided
        if params is None:
            params = {"formats": ["markdown"]}
        
        json_data = {"url": url}
        json_data.update(params)
        
        response = requests.post(
            f"{self.api_url}{endpoint}",
            headers=headers,
            json=json_data
        )
        
        if response.status_code == 200:
            return response.json().get("data", {})
        else:
            raise Exception(f"Scrape failed with status code {response.status_code}: {response.text}")
    
    def crawl_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Initiate a crawl job for the specified URL.
        
        Args:
            url: The URL to crawl.
            params: Additional parameters for the crawl request.
                excludePaths: List of URL pathname regex patterns to exclude
                includePaths: List of URL pathname regex patterns to include
                maxDepth: Maximum depth to crawl (default: 2)
                ignoreSitemap: Whether to ignore the sitemap (default: false)
                limit: Maximum number of pages to crawl (default: 10000)
                allowBackwardLinks: Allow backward links (default: false)
                allowExternalLinks: Allow external links (default: false)
                scrapeOptions: Options for scraping each page
            
        Returns:
            The crawl initiation response.
        """
        endpoint = "/v1/crawl"
        headers = self._prepare_headers()
        
        # Default parameters if none provided
        if params is None:
            params = {}
        
        json_data = {"url": url}
        json_data.update(params)
        
        response = requests.post(
            f"{self.api_url}{endpoint}",
            headers=headers,
            json=json_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Crawl initiation failed with status code {response.status_code}: {response.text}")
    
    def check_crawl_status(self, crawl_id: str) -> Dict[str, Any]:
        """
        Check the status of a crawl job.
        
        Args:
            crawl_id: The ID of the crawl job.
            
        Returns:
            The crawl status response.
        """
        endpoint = f"/v1/crawl/{crawl_id}"
        headers = self._prepare_headers()
        
        response = requests.get(
            f"{self.api_url}{endpoint}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Status check failed with status code {response.status_code}: {response.text}")
    
    def map_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map a URL to discover all links.
        
        Args:
            url: The URL to map.
            params: Additional parameters for the map request.
                search: Search query to filter results
                ignoreSitemap: Ignore the website sitemap (default: true)
                sitemapOnly: Only return links from sitemap (default: false)
                includeSubdomains: Include subdomains (default: false)
                limit: Maximum number of links to return (default: 5000)
                timeout: Timeout in milliseconds
            
        Returns:
            The map response.
        """
        endpoint = "/v1/map"
        headers = self._prepare_headers()
        
        # Default parameters if none provided
        if params is None:
            params = {}
        
        json_data = {"url": url}
        json_data.update(params)
        
        response = requests.post(
            f"{self.api_url}{endpoint}",
            headers=headers,
            json=json_data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Map failed with status code {response.status_code}: {response.text}")

    def wait_for_crawl_completion(self, crawl_id: str, poll_interval: int = 2, max_attempts: int = 30) -> Dict[str, Any]:
        """
        Wait for a crawl job to complete.
        
        Args:
            crawl_id: The ID of the crawl job.
            poll_interval: Time in seconds between status checks.
            max_attempts: Maximum number of status check attempts.
            
        Returns:
            The final crawl status response.
        """
        attempts = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Waiting for crawl to complete...", total=max_attempts)
            
            while attempts < max_attempts:
                status = self.check_crawl_status(crawl_id)
                
                if status.get("status") == "completed":
                    progress.update(task, completed=max_attempts)
                    return status
                
                attempts += 1
                progress.update(task, completed=attempts)
                time.sleep(poll_interval)
            
            raise Exception(f"Crawl did not complete within {max_attempts * poll_interval} seconds")

    def save_to_file(self, data: Any, directory: str, filename: str, format_type: str = "text") -> str:
        """
        Save data to a file in the specified directory with the given filename.
        
        Args:
            data: The data to save.
            directory: The directory to save the file in.
            filename: The name of the file.
            format_type: The format of the data (markdown, html, text, json).
            
        Returns:
            The full path to the saved file.
        """
        # Handle relative paths and ensure directory exists
        if not os.path.isabs(directory):
            # If not an absolute path, make it relative to the script's directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            directory = os.path.join(script_dir, directory)
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Add appropriate extension if not provided
        if not filename.endswith((".md", ".html", ".txt", ".json")):
            if format_type == "markdown":
                filename += ".md"
            elif format_type == "html":
                filename += ".html"
            elif format_type == "json":
                filename += ".json"
            else:
                filename += ".txt"
        
        # Create full path
        full_path = os.path.join(directory, filename)
        
        # Check if file already exists and handle conflicts
        if os.path.exists(full_path):
            # Get file name and extension
            base_name, extension = os.path.splitext(filename)
            counter = 1
            
            # Generate a new filename with a counter
            while os.path.exists(full_path):
                new_filename = f"{base_name}_{counter}{extension}"
                full_path = os.path.join(directory, new_filename)
                counter += 1
        
        # Save data to file
        with open(full_path, "w", encoding="utf-8") as f:
            if format_type == "json" and isinstance(data, dict):
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                f.write(str(data))
        
        return full_path


class FirecrawlExplorer:
    """A simple terminal UI for exploring Firecrawl functionality using Rich."""
    
    def __init__(self):
        """Initialize the Firecrawl Explorer."""
        self.console = Console()
        self.api_url = DEFAULT_API_URL
        self.api_key = ""
        self.client = FirecrawlClient(self.api_url, self.api_key if self.api_key else None)
        self.running = True
        
        # Set up default export directories
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.exports_base_dir = os.path.join(script_dir, "exports")
        
        # Create exports directory structure if it doesn't exist
        self._setup_export_directories()
        
        # Default save directory is now the exports folder
        self.default_save_dir = self.exports_base_dir
    
    def _setup_export_directories(self):
        """Set up the export directory structure."""
        # Create main exports directory
        os.makedirs(self.exports_base_dir, exist_ok=True)
        
        # Create subdirectories for different types of exports
        self.export_dirs = {
            "scrapes": os.path.join(self.exports_base_dir, "scrapes"),
            "crawls": os.path.join(self.exports_base_dir, "crawls"),
            "maps": os.path.join(self.exports_base_dir, "maps"),
            "docs": os.path.join(self.exports_base_dir, "docs"),
            "custom": os.path.join(self.exports_base_dir, "custom")
        }
        
        # Create each subdirectory
        for directory in self.export_dirs.values():
            os.makedirs(directory, exist_ok=True)
    
    def display_header(self):
        """Display the application header."""
        self.console.print(Panel.fit(
            "[bold green]🔥 Firecrawl Explorer[/bold green]",
            subtitle="A simple terminal UI for Firecrawl",
            box=box.ROUNDED
        ))
    
    def display_menu(self):
        """Display the main menu."""
        menu_table = Table(show_header=False, box=box.SIMPLE)
        menu_table.add_column("Key", style="cyan")
        menu_table.add_column("Action", style="green")
        
        menu_table.add_row("1", "Scrape URL")
        menu_table.add_row("2", "Crawl Website")
        menu_table.add_row("3", "Map Website")
        menu_table.add_row("4", "Settings")
        menu_table.add_row("5", "Help")
        menu_table.add_row("6", "Manage Exports")
        menu_table.add_row("q", "Quit")
        
        self.console.print(Panel(menu_table, title="Main Menu", box=box.ROUNDED))
    
    def display_welcome(self):
        """Display the welcome screen."""
        welcome_text = """
# Welcome to Firecrawl Explorer

This application allows you to interact with your local Firecrawl instance and explore its capabilities.

## Features:
- 🔍 **Scrape URL**: Extract content from a single webpage
- 🕸️ **Crawl Website**: Crawl an entire website and extract content from all pages
- 🗺️ **Map Website**: Discover all links on a website

## Getting Started:
1. Use the menu to navigate between different features
2. Configure your Firecrawl API URL in the Settings if needed
3. Start exploring the capabilities of your Firecrawl instance!
        """
        
        self.console.print(Panel(Markdown(welcome_text), box=box.ROUNDED))
    
    def scrape_url(self):
        """Handle the scrape URL functionality."""
        self.console.print(Panel.fit("[bold]🔍 Scrape URL[/bold]", box=box.ROUNDED))
        
        url = Prompt.ask("Enter the URL to scrape", default=DEFAULT_TEST_URL)
        format_options = ["markdown", "html", "text", "json"]
        
        # Display format options
        format_table = Table(show_header=False, box=box.SIMPLE)
        format_table.add_column("Key", style="cyan")
        format_table.add_column("Format", style="green")
        
        for i, fmt in enumerate(format_options, 1):
            format_table.add_row(str(i), fmt)
        
        self.console.print(Panel(format_table, title="Select Output Format", box=box.ROUNDED))
        
        # Get user choice
        choice = Prompt.ask("Choose a format", choices=["1", "2", "3", "4"], default="1")
        format_value = format_options[int(choice) - 1]
        
        # Ask for main content only
        only_main_content = Confirm.ask("Extract only main content?", default=True)
        
        # Execute scrape with a single progress display
        self.console.print("[cyan]Scraping URL...[/cyan]")
        
        try:
            params = {
                "formats": [format_value],
                "onlyMainContent": only_main_content
            }
            result = self.client.scrape_url(url, params)
            
            if format_value == "markdown":
                content = result.get("markdown", "No markdown content returned")
                self.console.print(Panel(Markdown(content), title=f"Scrape Results for {url}", box=box.ROUNDED))
            elif format_value == "html":
                content = result.get("html", "No HTML content returned")
                self.console.print(Panel(Syntax(content, "html", theme="monokai", line_numbers=True), title=f"Scrape Results for {url}", box=box.ROUNDED))
            elif format_value == "json":
                content = json.dumps(result.get("json", {}), indent=2)
                self.console.print(Panel(Syntax(content, "json", theme="monokai", line_numbers=True), title=f"Scrape Results for {url}", box=box.ROUNDED))
            else:
                content = result.get("text", "No text content returned")
                self.console.print(Panel(content, title=f"Scrape Results for {url}", box=box.ROUNDED))
            
            # Display metadata
            if "metadata" in result:
                metadata_table = Table(title="Metadata", box=box.ROUNDED)
                metadata_table.add_column("Property", style="cyan")
                metadata_table.add_column("Value", style="green")
                
                for key, value in result["metadata"].items():
                    if value is not None:
                        metadata_table.add_row(key, str(value))
                
                self.console.print(metadata_table)
            
            # Ask if user wants to save the results
            if Confirm.ask("Do you want to save these results to a file?", default=True):
                # Prepare the data to save based on format
                if format_value == "json":
                    save_data = result.get("json", {})
                elif format_value == "markdown":
                    save_data = result.get("markdown", "")
                elif format_value == "html":
                    save_data = result.get("html", "")
                else:
                    save_data = result.get("text", "")
                
                # Use the helper method to handle the save dialog
                self._handle_save_dialog(save_data, url, "", format_value)
        
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        # Improved user prompt
        self.console.print("\n[bold cyan]Press Enter to return to the main menu...[/bold cyan]")
        try:
            input()
        except EOFError:
            pass  # Handle potential EOFError when running in certain environments
    
    def crawl_url(self):
        """Handle the crawl URL functionality."""
        self.console.print(Panel.fit("[bold]🕸️ Crawl Website[/bold]", box=box.ROUNDED))
        
        url = Prompt.ask("Enter the URL to crawl", default=DEFAULT_TEST_URL)
        exclude_paths = Prompt.ask("Exclude paths (comma-separated)", default="")
        include_paths = Prompt.ask("Include paths (comma-separated)", default="")
        depth = Prompt.ask("Maximum depth", default="2")
        limit = Prompt.ask("Maximum pages to crawl", default="100")
        
        # Execute crawl with a single progress display
        self.console.print("[cyan]Initiating crawl...[/cyan]")
        
        try:
            params = {
                "maxDepth": int(depth),
                "limit": int(limit),
                "scrapeOptions": {
                    "formats": ["markdown"],
                    "onlyMainContent": True
                }
            }
            
            if exclude_paths:
                params["excludePaths"] = [path.strip() for path in exclude_paths.split(",")]
            
            if include_paths:
                params["includePaths"] = [path.strip() for path in include_paths.split(",")]
            
            crawl_response = self.client.crawl_url(url, params)
            crawl_id = crawl_response.get("id")
            
            if not crawl_id:
                self.console.print("[bold red]Error:[/bold red] No crawl ID returned")
                return
            
            self.console.print(f"[cyan]Crawl initiated with ID: {crawl_id}[/cyan]")
            self.console.print("[cyan]Waiting for crawl to complete...[/cyan]")
            
            # Wait for crawl completion
            final_status = self.client.wait_for_crawl_completion(crawl_id)
            
            # Create a table to display the results
            table = Table(title=f"Crawl Results for {url}", box=box.ROUNDED)
            table.add_column("URL", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Content Length", style="yellow")
            
            data = final_status.get("data", [])
            for item in data:
                page_url = item.get("metadata", {}).get("sourceURL", "Unknown")
                status = "Success"
                content_length = len(item.get("markdown", "")) if "markdown" in item else 0
                table.add_row(page_url, status, str(content_length))
            
            self.console.print(table)
            
            # Ask if user wants to save the results
            if Confirm.ask("Do you want to save the crawl results to a file?", default=True):
                # Use the helper method to handle the save dialog
                self._handle_save_dialog(final_status, url, "crawl_", "json")
        
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        # Improved user prompt
        self.console.print("\n[bold cyan]Press Enter to return to the main menu...[/bold cyan]")
        try:
            input()
        except EOFError:
            pass  # Handle potential EOFError when running in certain environments
    
    def map_url(self):
        """Handle the map URL functionality."""
        self.console.print(Panel.fit("[bold]🗺️ Map Website[/bold]", box=box.ROUNDED))
        
        url = Prompt.ask("Enter the URL to map", default=DEFAULT_TEST_URL)
        search_term = Prompt.ask("Search term (optional)", default="")
        include_subdomains = Confirm.ask("Include subdomains?", default=False)
        limit = Prompt.ask("Maximum links to return", default="100")
        
        # Execute map with a single progress display
        self.console.print("[cyan]Mapping URL...[/cyan]")
        
        try:
            params = {
                "includeSubdomains": include_subdomains,
                "limit": int(limit)
            }
            
            if search_term:
                params["search"] = search_term
            
            result = self.client.map_url(url, params)
            
            # Create a table to display the results
            table = Table(title=f"Map Results for {url}", box=box.ROUNDED)
            table.add_column("URL", style="cyan")
            
            links = result.get("links", [])
            for link in links:
                table.add_row(link)
            
            self.console.print(table)
            self.console.print(f"[bold green]Total links found:[/bold green] {len(links)}")
            
            # Ask if user wants to save the results
            if Confirm.ask("Do you want to save the map results to a file?", default=True):
                # Format links as a list for better readability
                links_data = {"url": url, "links": links, "total": len(links)}
                
                # Use the helper method to handle the save dialog
                self._handle_save_dialog(links_data, url, "map_", "json")
        
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        # Improved user prompt
        self.console.print("\n[bold cyan]Press Enter to return to the main menu...[/bold cyan]")
        try:
            input()
        except EOFError:
            pass  # Handle potential EOFError when running in certain environments
    
    def settings(self):
        """Handle the settings functionality."""
        self.console.print(Panel.fit("[bold]⚙️ Settings[/bold]", box=box.ROUNDED))
        
        current_settings = Table(show_header=False, box=box.SIMPLE)
        current_settings.add_column("Setting", style="cyan")
        current_settings.add_column("Value", style="green")
        current_settings.add_row("API URL", self.api_url)
        current_settings.add_row("API Key", "*****" if self.api_key else "Not set")
        current_settings.add_row("Default Exports Directory", self.exports_base_dir)
        
        # Add export subdirectories to the settings table
        for name, path in self.export_dirs.items():
            current_settings.add_row(f"{name.capitalize()} Directory", path)
        
        self.console.print(Panel(current_settings, title="Current Settings", box=box.ROUNDED))
        
        if Confirm.ask("Do you want to update these settings?"):
            new_api_url = Prompt.ask("Firecrawl API URL", default=self.api_url)
            new_api_key = Prompt.ask("API Key (optional for self-hosted)", default=self.api_key, password=True)
            
            # Update exports base directory
            new_exports_base = Prompt.ask("Default Exports Directory", default=self.exports_base_dir)
            
            # Apply changes
            self.api_url = new_api_url
            self.api_key = new_api_key
            
            # Update exports directory if changed
            if new_exports_base != self.exports_base_dir:
                self.exports_base_dir = new_exports_base
                self.default_save_dir = self.exports_base_dir
                
                # Re-setup export directories with the new base
                self._setup_export_directories()
            
            self.client = FirecrawlClient(self.api_url, self.api_key if self.api_key else None)
            
            # Create the export directories if they don't exist
            try:
                self._setup_export_directories()
                self.console.print("[bold green]Settings saved successfully![/bold green]")
            except Exception as e:
                self.console.print(f"[bold red]Error creating export directories:[/bold red] {str(e)}")
        
        # Improved user prompt
        self.console.print("\n[bold cyan]Press Enter to return to the main menu...[/bold cyan]")
        try:
            input()
        except EOFError:
            pass  # Handle potential EOFError when running in certain environments
    
    def help(self):
        """Display help information."""
        help_text = """
## Keyboard Shortcuts:
- `1`: Go to Scrape URL
- `2`: Go to Crawl Website
- `3`: Go to Map Website
- `4`: Go to Settings
- `5`: Show this help
- `6`: Manage Exports
- `q`: Quit the application

## About Firecrawl:
Firecrawl is an API service that takes a URL, crawls it, and converts it into clean markdown or structured data. It crawls all accessible subpages and gives you clean data for each.

## Self-hosted Instance:
You are currently using a self-hosted instance of Firecrawl. This means that all data processing happens locally on your machine.

## Export System:
The export system organizes your data into different categories:
- **Scrapes**: Single page scraping results
- **Crawls**: Multi-page crawling results
- **Maps**: Website mapping results
- **Docs**: Documentation and guides
- **Custom**: Any other exports
        """
        
        self.console.print(Panel(Markdown(help_text), title="Help", box=box.ROUNDED))
        
        # Add option to save documentation
        if Confirm.ask("Would you like to save this documentation to the docs folder?", default=False):
            # Create documentation with more detailed information
            full_docs = f"""# Firecrawl Explorer Documentation

## Overview
Firecrawl Explorer is a terminal-based UI for interacting with a self-hosted Firecrawl instance.
This tool allows you to scrape websites, crawl entire domains, and map website structures.

## Features

### Scrape URL
Extract content from a single webpage in various formats:
- Markdown: Clean, readable text format
- HTML: Structured HTML content
- Text: Plain text content
- JSON: Structured data format

### Crawl Website
Crawl an entire website and extract content from all pages. This feature:
- Follows links within the domain
- Processes each page
- Returns a structured dataset of all crawled pages

### Map Website
Discover all links on a website. Options include:
- Including/excluding subdomains
- Searching for specific terms
- Limiting the number of results

### Export System
All results can be saved to the exports directory, organized by type:
- **{self.export_dirs["scrapes"]}**: Single page scraping results
- **{self.export_dirs["crawls"]}**: Multi-page crawling results
- **{self.export_dirs["maps"]}**: Website mapping results
- **{self.export_dirs["docs"]}**: Documentation and guides
- **{self.export_dirs["custom"]}**: Any other exports

### Metadata
You can add metadata to your exports:
- Descriptions
- Tags
- Export date and time
- Source URL

## Configuration
Configure your Firecrawl instance in the Settings menu:
- API URL: {self.api_url}
- API Key: {"Set" if self.api_key else "Not set"}
- Export Directories: Customizable locations for saved data

## Keyboard Shortcuts
- `1`: Go to Scrape URL
- `2`: Go to Crawl Website
- `3`: Go to Map Website
- `4`: Go to Settings
- `5`: Show this help
- `6`: Manage Exports
- `q`: Quit the application

## Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            # Save the documentation
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"firecrawl_explorer_docs_{timestamp}"
            
            try:
                saved_path = self.client.save_to_file(
                    full_docs, 
                    self.export_dirs["docs"], 
                    filename, 
                    "markdown"
                )
                
                self.console.print(f"[bold green]Documentation saved to:[/bold green] {saved_path}")
                
                # Offer to open the documentation
                if Confirm.ask("Would you like to open the documentation?", default=True):
                    try:
                        # Use the appropriate command based on the OS
                        if sys.platform == "win32":
                            os.startfile(saved_path)
                        elif sys.platform == "darwin":  # macOS
                            os.system(f"open '{saved_path}'")
                        else:  # Linux
                            os.system(f"xdg-open '{saved_path}'")
                    except Exception as e:
                        self.console.print(f"[yellow]Could not open documentation: {str(e)}[/yellow]")
            except Exception as e:
                self.console.print(f"[bold red]Error saving documentation:[/bold red] {str(e)}")
        
        # Improved user prompt
        self.console.print("\n[bold cyan]Press Enter to return to the main menu...[/bold cyan]")
        try:
            input()
        except EOFError:
            pass  # Handle potential EOFError when running in certain environments
    
    def manage_exports(self):
        """Browse and manage saved exports."""
        self.console.print(Panel.fit("[bold]📁 Manage Exports[/bold]", box=box.ROUNDED))
        
        # Create a table for export categories
        categories_table = Table(show_header=False, box=box.SIMPLE)
        categories_table.add_column("Key", style="cyan")
        categories_table.add_column("Category", style="green")
        categories_table.add_column("Count", style="yellow")
        
        # Count files in each export directory
        file_counts = {}
        for name, path in self.export_dirs.items():
            try:
                # Count only files, not directories
                count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                file_counts[name] = count
            except FileNotFoundError:
                file_counts[name] = 0
        
        # Add all categories to the table
        for i, (name, path) in enumerate(self.export_dirs.items(), 1):
            categories_table.add_row(str(i), name.capitalize(), str(file_counts[name]))
        
        # Add option for all exports
        total_files = sum(file_counts.values())
        categories_table.add_row(str(len(self.export_dirs) + 1), "All Exports", str(total_files))
        
        self.console.print(Panel(categories_table, title="Export Categories", box=box.ROUNDED))
        
        # Get user choice
        choices = [str(i) for i in range(1, len(self.export_dirs) + 2)]
        category_choice = Prompt.ask("Select a category to browse", choices=choices, default="1")
        
        # Determine which directory to browse
        if category_choice == str(len(self.export_dirs) + 1):
            # Browse all exports
            self._browse_exports("All Exports", None)
        else:
            # Browse specific category
            category_index = int(category_choice) - 1
            category_name = list(self.export_dirs.keys())[category_index]
            category_path = self.export_dirs[category_name]
            self._browse_exports(category_name.capitalize(), category_path)
        
        # Improved user prompt
        self.console.print("\n[bold cyan]Press Enter to return to the main menu...[/bold cyan]")
        try:
            input()
        except EOFError:
            pass  # Handle potential EOFError when running in certain environments
    
    def _browse_exports(self, category_name: str, category_path: Optional[str]):
        """
        Browse exports in a specific category or all exports.
        
        Args:
            category_name: The name of the category to browse.
            category_path: The path to the category directory, or None for all exports.
        """
        self.console.print(Panel.fit(f"[bold]📁 Browsing {category_name}[/bold]", box=box.ROUNDED))
        
        # Collect all files
        files = []
        if category_path is None:
            # Collect files from all export directories
            for name, path in self.export_dirs.items():
                try:
                    for filename in os.listdir(path):
                        file_path = os.path.join(path, filename)
                        if os.path.isfile(file_path) and not filename.endswith(".meta.json"):
                            # Get file info
                            file_info = {
                                "name": filename,
                                "path": file_path,
                                "category": name,
                                "size": os.path.getsize(file_path),
                                "modified": os.path.getmtime(file_path)
                            }
                            
                            # Try to get metadata if available
                            meta_path = f"{os.path.splitext(file_path)[0]}.meta.json"
                            if os.path.exists(meta_path):
                                try:
                                    with open(meta_path, "r", encoding="utf-8") as f:
                                        metadata = json.load(f)
                                        file_info["metadata"] = metadata
                                except Exception:
                                    pass
                            
                            files.append(file_info)
                except FileNotFoundError:
                    continue
        else:
            # Collect files from the specific category
            try:
                for filename in os.listdir(category_path):
                    file_path = os.path.join(category_path, filename)
                    if os.path.isfile(file_path) and not filename.endswith(".meta.json"):
                        # Get file info
                        file_info = {
                            "name": filename,
                            "path": file_path,
                            "category": category_name.lower(),
                            "size": os.path.getsize(file_path),
                            "modified": os.path.getmtime(file_path)
                        }
                        
                        # Try to get metadata if available
                        meta_path = f"{os.path.splitext(file_path)[0]}.meta.json"
                        if os.path.exists(meta_path):
                            try:
                                with open(meta_path, "r", encoding="utf-8") as f:
                                    metadata = json.load(f)
                                    file_info["metadata"] = metadata
                            except Exception:
                                pass
                        
                        files.append(file_info)
            except FileNotFoundError:
                pass
        
        # Sort files by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        if not files:
            self.console.print("[yellow]No exports found in this category.[/yellow]")
            return
        
        # Create a table to display the files
        files_table = Table(box=box.ROUNDED)
        files_table.add_column("#", style="cyan")
        files_table.add_column("Filename", style="green")
        files_table.add_column("Category", style="blue")
        files_table.add_column("Size", style="yellow")
        files_table.add_column("Date", style="magenta")
        files_table.add_column("Description", style="white")
        
        # Add files to the table
        for i, file_info in enumerate(files[:20], 1):  # Limit to 20 files for readability
            # Format size
            size_kb = file_info["size"] / 1024
            size_str = f"{size_kb:.1f} KB"
            
            # Format date
            date_str = datetime.fromtimestamp(file_info["modified"]).strftime("%Y-%m-%d %H:%M")
            
            # Get description if available
            description = ""
            if "metadata" in file_info and "description" in file_info["metadata"]:
                description = file_info["metadata"]["description"]
                if len(description) > 30:
                    description = description[:27] + "..."
            
            files_table.add_row(
                str(i),
                file_info["name"],
                file_info["category"].capitalize(),
                size_str,
                date_str,
                description
            )
        
        self.console.print(files_table)
        
        if len(files) > 20:
            self.console.print(f"[yellow]Showing 20 of {len(files)} files. Use search to find specific files.[/yellow]")
        
        # Options for file management
        options_table = Table(show_header=False, box=box.SIMPLE)
        options_table.add_column("Key", style="cyan")
        options_table.add_column("Action", style="green")
        
        options_table.add_row("v", "View file")
        options_table.add_row("o", "Open containing folder")
        options_table.add_row("d", "Delete file")
        options_table.add_row("s", "Search files")
        options_table.add_row("r", "Return to categories")
        
        self.console.print(Panel(options_table, title="File Management Options", box=box.ROUNDED))
        
        # Get user choice
        action_choice = Prompt.ask("Select an action", choices=["v", "o", "d", "s", "r"], default="r")
        
        if action_choice == "r":
            return
        elif action_choice == "s":
            # Search functionality
            search_term = Prompt.ask("Enter search term")
            search_results = []
            
            for file_info in files:
                # Search in filename
                if search_term.lower() in file_info["name"].lower():
                    search_results.append(file_info)
                    continue
                
                # Search in metadata
                if "metadata" in file_info:
                    metadata = file_info["metadata"]
                    
                    # Search in description
                    if "description" in metadata and search_term.lower() in metadata["description"].lower():
                        search_results.append(file_info)
                        continue
                    
                    # Search in tags
                    if "tags" in metadata and any(search_term.lower() in tag.lower() for tag in metadata["tags"]):
                        search_results.append(file_info)
                        continue
                    
                    # Search in source URL
                    if "source_url" in metadata and search_term.lower() in metadata["source_url"].lower():
                        search_results.append(file_info)
                        continue
            
            if search_results:
                self.console.print(f"[green]Found {len(search_results)} matching files.[/green]")
                # Recursively call with search results
                self._display_and_manage_files(search_results, f"Search Results for '{search_term}'")
            else:
                self.console.print("[yellow]No matching files found.[/yellow]")
                # Return to file browsing
                self._browse_exports(category_name, category_path)
        elif action_choice == "v":
            # View file
            file_num = Prompt.ask("Enter file number to view", default="1")
            try:
                file_index = int(file_num) - 1
                if 0 <= file_index < len(files):
                    self._view_file(files[file_index])
                else:
                    self.console.print("[yellow]Invalid file number.[/yellow]")
            except ValueError:
                self.console.print("[yellow]Invalid input. Please enter a number.[/yellow]")
            
            # Return to file browsing
            self._browse_exports(category_name, category_path)
        elif action_choice == "o":
            # Open containing folder
            try:
                folder_path = category_path if category_path else self.exports_base_dir
                
                # Use the appropriate command based on the OS
                if sys.platform == "win32":
                    os.startfile(folder_path)
                elif sys.platform == "darwin":  # macOS
                    os.system(f"open '{folder_path}'")
                else:  # Linux
                    os.system(f"xdg-open '{folder_path}'")
                
                self.console.print(f"[green]Opened folder: {folder_path}[/green]")
            except Exception as e:
                self.console.print(f"[yellow]Could not open folder: {str(e)}[/yellow]")
            
            # Return to file browsing
            self._browse_exports(category_name, category_path)
        elif action_choice == "d":
            # Delete file
            file_num = Prompt.ask("Enter file number to delete", default="1")
            try:
                file_index = int(file_num) - 1
                if 0 <= file_index < len(files):
                    file_info = files[file_index]
                    file_path = file_info["path"]
                    
                    if Confirm.ask(f"Are you sure you want to delete '{file_info['name']}'?", default=False):
                        try:
                            # Delete the file
                            os.remove(file_path)
                            
                            # Delete metadata file if it exists
                            meta_path = f"{os.path.splitext(file_path)[0]}.meta.json"
                            if os.path.exists(meta_path):
                                os.remove(meta_path)
                            
                            self.console.print(f"[green]File deleted: {file_info['name']}[/green]")
                        except Exception as e:
                            self.console.print(f"[yellow]Could not delete file: {str(e)}[/yellow]")
                else:
                    self.console.print("[yellow]Invalid file number.[/yellow]")
            except ValueError:
                self.console.print("[yellow]Invalid input. Please enter a number.[/yellow]")
            
            # Return to file browsing
            self._browse_exports(category_name, category_path)
    
    def _display_and_manage_files(self, files, title):
        """
        Display and manage a list of files.
        
        Args:
            files: List of file info dictionaries.
            title: Title for the file list.
        """
        self.console.print(Panel.fit(f"[bold]📁 {title}[/bold]", box=box.ROUNDED))
        
        # Create a table to display the files
        files_table = Table(box=box.ROUNDED)
        files_table.add_column("#", style="cyan")
        files_table.add_column("Filename", style="green")
        files_table.add_column("Category", style="blue")
        files_table.add_column("Size", style="yellow")
        files_table.add_column("Date", style="magenta")
        files_table.add_column("Description", style="white")
        
        # Add files to the table
        for i, file_info in enumerate(files[:20], 1):  # Limit to 20 files for readability
            # Format size
            size_kb = file_info["size"] / 1024
            size_str = f"{size_kb:.1f} KB"
            
            # Format date
            date_str = datetime.fromtimestamp(file_info["modified"]).strftime("%Y-%m-%d %H:%M")
            
            # Get description if available
            description = ""
            if "metadata" in file_info and "description" in file_info["metadata"]:
                description = file_info["metadata"]["description"]
                if len(description) > 30:
                    description = description[:27] + "..."
            
            files_table.add_row(
                str(i),
                file_info["name"],
                file_info["category"].capitalize(),
                size_str,
                date_str,
                description
            )
        
        self.console.print(files_table)
        
        # Options for file management
        options_table = Table(show_header=False, box=box.SIMPLE)
        options_table.add_column("Key", style="cyan")
        options_table.add_column("Action", style="green")
        
        options_table.add_row("v", "View file")
        options_table.add_row("r", "Return")
        
        self.console.print(Panel(options_table, title="Options", box=box.ROUNDED))
        
        # Get user choice
        action_choice = Prompt.ask("Select an action", choices=["v", "r"], default="r")
        
        if action_choice == "v":
            # View file
            file_num = Prompt.ask("Enter file number to view", default="1")
            try:
                file_index = int(file_num) - 1
                if 0 <= file_index < len(files):
                    self._view_file(files[file_index])
                else:
                    self.console.print("[yellow]Invalid file number.[/yellow]")
            except ValueError:
                self.console.print("[yellow]Invalid input. Please enter a number.[/yellow]")
            
            # Return to file display
            self._display_and_manage_files(files, title)
    
    def _view_file(self, file_info):
        """
        View the contents of a file.
        
        Args:
            file_info: Dictionary containing file information.
        """
        file_path = file_info["path"]
        file_name = file_info["name"]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Determine the file type
            if file_name.endswith(".json"):
                # Parse and pretty-print JSON
                try:
                    parsed_json = json.loads(content)
                    content = json.dumps(parsed_json, indent=2)
                    syntax = Syntax(content, "json", theme="monokai", line_numbers=True)
                except json.JSONDecodeError:
                    syntax = Syntax(content, "text", theme="monokai", line_numbers=True)
            elif file_name.endswith(".md"):
                # Render markdown
                self.console.print(Panel(Markdown(content), title=file_name, box=box.ROUNDED))
                return
            elif file_name.endswith(".html"):
                syntax = Syntax(content, "html", theme="monokai", line_numbers=True)
            else:
                syntax = Syntax(content, "text", theme="monokai", line_numbers=True)
            
            # Display file content with syntax highlighting
            self.console.print(Panel(syntax, title=file_name, box=box.ROUNDED))
            
            # Display metadata if available
            if "metadata" in file_info:
                metadata = file_info["metadata"]
                
                metadata_table = Table(show_header=False, box=box.SIMPLE)
                metadata_table.add_column("Property", style="cyan")
                metadata_table.add_column("Value", style="green")
                
                if "description" in metadata and metadata["description"]:
                    metadata_table.add_row("Description", metadata["description"])
                
                if "tags" in metadata and metadata["tags"]:
                    metadata_table.add_row("Tags", ", ".join(metadata["tags"]))
                
                if "export_date" in metadata:
                    metadata_table.add_row("Export Date", metadata["export_date"])
                
                if "source_url" in metadata:
                    metadata_table.add_row("Source URL", metadata["source_url"])
                
                if metadata_table.row_count > 0:
                    self.console.print(Panel(metadata_table, title="Metadata", box=box.ROUNDED))
        
        except Exception as e:
            self.console.print(f"[yellow]Could not read file: {str(e)}[/yellow]")
    
    def _handle_save_dialog(self, data, url, prefix="", format_type="json"):
        """
        Handle the save dialog consistently across all functions.
        
        Args:
            data: The data to save.
            url: The URL that was processed.
            prefix: A prefix for the filename (e.g., "crawl_", "map_").
            format_type: The format to save the data in.
            
        Returns:
            bool: Whether the save was successful.
        """
        # Determine the export type based on the prefix
        export_type = "custom"
        if prefix == "crawl_":
            export_type = "crawls"
        elif prefix == "map_":
            export_type = "maps"
        elif prefix == "":
            export_type = "scrapes"
        
        # Display save options in a panel
        self.console.print(Panel("[bold]Save Options[/bold]", box=box.ROUNDED))
        
        # Create a table for save location options
        save_options = Table(show_header=False, box=box.SIMPLE)
        save_options.add_column("Option", style="cyan")
        save_options.add_column("Location", style="green")
        
        save_options.add_row("1", f"Default ({self.export_dirs[export_type]})")
        save_options.add_row("2", f"Main exports folder ({self.exports_base_dir})")
        
        for i, (name, path) in enumerate(self.export_dirs.items(), 3):
            if name != export_type:  # Skip the default one as it's already option 1
                save_options.add_row(str(i), f"{name.capitalize()} folder ({path})")
        
        save_options.add_row(str(len(self.export_dirs) + 2), "Custom location")
        
        self.console.print(Panel(save_options, title="Choose Save Location", box=box.ROUNDED))
        
        # Get user choice
        choices = [str(i) for i in range(1, len(self.export_dirs) + 3)]
        dir_choice = Prompt.ask("Select save location", choices=choices, default="1")
        
        # Set the save directory based on user choice
        if dir_choice == "1":
            save_dir = self.export_dirs[export_type]
        elif dir_choice == "2":
            save_dir = self.exports_base_dir
        elif dir_choice == str(len(self.export_dirs) + 2):
            save_dir = Prompt.ask("Enter custom directory path", default=self.default_save_dir)
        else:
            # Get the directory name from the option number
            dir_index = int(dir_choice) - 3
            dir_name = list(self.export_dirs.keys())[dir_index]
            save_dir = self.export_dirs[dir_name]
        
        # Generate default filename based on URL and timestamp
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{prefix}{domain}_{timestamp}"
        
        # Ask for filename
        filename = Prompt.ask("Enter filename (without extension)", default=default_filename)
        
        # Ask for optional description/tags
        add_metadata = Confirm.ask("Add description or tags to this export?", default=False)
        metadata = {}
        
        if add_metadata:
            description = Prompt.ask("Enter a description (optional)", default="")
            tags = Prompt.ask("Enter tags separated by commas (optional)", default="")
            
            if description:
                metadata["description"] = description
            if tags:
                metadata["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
            
            # If we have metadata and the format is JSON, add it to the data
            if metadata and format_type == "json" and isinstance(data, dict):
                if "metadata" not in data:
                    data["metadata"] = {}
                data["metadata"].update({
                    "export_info": metadata,
                    "export_date": datetime.now().isoformat(),
                    "source_url": url
                })
        
        # Save the content
        try:
            saved_path = self.client.save_to_file(data, save_dir, filename, format_type)
            
            # Create a metadata sidecar file for non-JSON formats
            if metadata and (format_type != "json" or not isinstance(data, dict)):
                metadata_file = f"{os.path.splitext(saved_path)[0]}.meta.json"
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "description": metadata.get("description", ""),
                        "tags": metadata.get("tags", []),
                        "export_date": datetime.now().isoformat(),
                        "source_url": url,
                        "format": format_type
                    }, f, indent=2)
            
            self.console.print(f"[bold green]Results saved to:[/bold green] {saved_path}")
            
            # Offer to open the directory
            if Confirm.ask("Open the directory containing this file?", default=False):
                try:
                    # Use the appropriate command based on the OS
                    if sys.platform == "win32":
                        os.startfile(save_dir)
                    elif sys.platform == "darwin":  # macOS
                        os.system(f"open '{save_dir}'")
                    else:  # Linux
                        os.system(f"xdg-open '{save_dir}'")
                except Exception as e:
                    self.console.print(f"[yellow]Could not open directory: {str(e)}[/yellow]")
            
            return True
        except Exception as e:
            self.console.print(f"[bold red]Error saving file:[/bold red] {str(e)}")
            return False
    
    def run(self):
        """Run the application."""
        self.console.clear()
        
        while self.running:
            self.console.clear()
            self.display_header()
            self.display_welcome()
            self.display_menu()
            
            try:
                choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6", "q"], default="1")
                
                if choice == "1":
                    self.scrape_url()
                elif choice == "2":
                    self.crawl_url()
                elif choice == "3":
                    self.map_url()
                elif choice == "4":
                    self.settings()
                elif choice == "5":
                    self.help()
                elif choice == "6":
                    self.manage_exports()
                elif choice.lower() == "q":
                    self.running = False
                    self.console.print("[bold green]Thank you for using Firecrawl Explorer![/bold green]")
                    break
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                self.running = False
                self.console.print("\n[bold yellow]Exiting Firecrawl Explorer...[/bold yellow]")
                break
            except Exception as e:
                # Handle any other unexpected errors
                self.console.print(f"\n[bold red]An error occurred:[/bold red] {str(e)}")
                self.console.print("[bold cyan]Press Enter to continue...[/bold cyan]")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    self.running = False
                    break


def main():
    """Main entry point."""
    explorer = FirecrawlExplorer()
    explorer.run()


if __name__ == "__main__":
    main()