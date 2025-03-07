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
        
        # Save data to file
        with open(full_path, "w", encoding="utf-8") as f:
            if format_type == "json" and isinstance(data, dict):
                json.dump(data, f, indent=2)
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
        self.default_save_dir = os.path.join(os.path.expanduser("~"), "firecrawl_data")
    
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
        
        # Execute scrape
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Scraping URL...", total=1)
            
            try:
                params = {
                    "formats": [format_value],
                    "onlyMainContent": only_main_content
                }
                result = self.client.scrape_url(url, params)
                progress.update(task, completed=1)
                
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
                    # Ask for directory
                    save_dir = Prompt.ask("Enter directory to save file", default=self.default_save_dir)
                    
                    # Generate default filename based on URL and timestamp
                    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    default_filename = f"{domain}_{timestamp}"
                    
                    # Ask for filename
                    filename = Prompt.ask("Enter filename", default=default_filename)
                    
                    # Save the content
                    if format_value == "json":
                        save_data = result.get("json", {})
                    else:
                        save_data = content
                    
                    try:
                        saved_path = self.client.save_to_file(save_data, save_dir, filename, format_value)
                        self.console.print(f"[bold green]Results saved to:[/bold green] {saved_path}")
                    except Exception as e:
                        self.console.print(f"[bold red]Error saving file:[/bold red] {str(e)}")
            
            except Exception as e:
                progress.update(task, completed=1)
                self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        self.console.print("\nPress Enter to continue...")
        input()
    
    def crawl_url(self):
        """Handle the crawl URL functionality."""
        self.console.print(Panel.fit("[bold]🕸️ Crawl Website[/bold]", box=box.ROUNDED))
        
        url = Prompt.ask("Enter the URL to crawl", default=DEFAULT_TEST_URL)
        exclude_paths = Prompt.ask("Exclude paths (comma-separated)", default="")
        include_paths = Prompt.ask("Include paths (comma-separated)", default="")
        depth = Prompt.ask("Maximum depth", default="2")
        limit = Prompt.ask("Maximum pages to crawl", default="100")
        
        # Execute crawl
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Initiating crawl...", total=1)
            
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
                progress.update(task, completed=1)
                
                if not crawl_id:
                    self.console.print("[bold red]Error:[/bold red] No crawl ID returned")
                    return
                
                self.console.print(f"Crawl initiated with ID: {crawl_id}")
                
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
                    # Ask for directory
                    save_dir = Prompt.ask("Enter directory to save file", default=self.default_save_dir)
                    
                    # Generate default filename based on URL and timestamp
                    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    default_filename = f"crawl_{domain}_{timestamp}"
                    
                    # Ask for filename
                    filename = Prompt.ask("Enter filename", default=default_filename)
                    
                    # Save the content
                    try:
                        saved_path = self.client.save_to_file(final_status, save_dir, filename, "json")
                        self.console.print(f"[bold green]Results saved to:[/bold green] {saved_path}")
                    except Exception as e:
                        self.console.print(f"[bold red]Error saving file:[/bold red] {str(e)}")
            
            except Exception as e:
                progress.update(task, completed=1)
                self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        self.console.print("\nPress Enter to continue...")
        input()
    
    def map_url(self):
        """Handle the map URL functionality."""
        self.console.print(Panel.fit("[bold]🗺️ Map Website[/bold]", box=box.ROUNDED))
        
        url = Prompt.ask("Enter the URL to map", default=DEFAULT_TEST_URL)
        search_term = Prompt.ask("Search term (optional)", default="")
        include_subdomains = Confirm.ask("Include subdomains?", default=False)
        limit = Prompt.ask("Maximum links to return", default="100")
        
        # Execute map
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Mapping URL...", total=1)
            
            try:
                params = {
                    "includeSubdomains": include_subdomains,
                    "limit": int(limit)
                }
                
                if search_term:
                    params["search"] = search_term
                
                result = self.client.map_url(url, params)
                progress.update(task, completed=1)
                
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
                    # Ask for directory
                    save_dir = Prompt.ask("Enter directory to save file", default=self.default_save_dir)
                    
                    # Generate default filename based on URL and timestamp
                    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    default_filename = f"map_{domain}_{timestamp}"
                    
                    # Ask for filename
                    filename = Prompt.ask("Enter filename", default=default_filename)
                    
                    # Save the content
                    try:
                        # Format links as a list for better readability
                        links_data = {"url": url, "links": links, "total": len(links)}
                        saved_path = self.client.save_to_file(links_data, save_dir, filename, "json")
                        self.console.print(f"[bold green]Results saved to:[/bold green] {saved_path}")
                    except Exception as e:
                        self.console.print(f"[bold red]Error saving file:[/bold red] {str(e)}")
            
            except Exception as e:
                progress.update(task, completed=1)
                self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        self.console.print("\nPress Enter to continue...")
        input()
    
    def settings(self):
        """Handle the settings functionality."""
        self.console.print(Panel.fit("[bold]⚙️ Settings[/bold]", box=box.ROUNDED))
        
        current_settings = Table(show_header=False, box=box.SIMPLE)
        current_settings.add_column("Setting", style="cyan")
        current_settings.add_column("Value", style="green")
        current_settings.add_row("API URL", self.api_url)
        current_settings.add_row("API Key", "*****" if self.api_key else "Not set")
        current_settings.add_row("Default Save Directory", self.default_save_dir)
        
        self.console.print(Panel(current_settings, title="Current Settings", box=box.ROUNDED))
        
        if Confirm.ask("Do you want to update these settings?"):
            new_api_url = Prompt.ask("Firecrawl API URL", default=self.api_url)
            new_api_key = Prompt.ask("API Key (optional for self-hosted)", default=self.api_key, password=True)
            new_save_dir = Prompt.ask("Default Save Directory", default=self.default_save_dir)
            
            self.api_url = new_api_url
            self.api_key = new_api_key
            self.default_save_dir = new_save_dir
            self.client = FirecrawlClient(self.api_url, self.api_key if self.api_key else None)
            
            # Create the default save directory if it doesn't exist
            try:
                os.makedirs(self.default_save_dir, exist_ok=True)
                self.console.print("[bold green]Settings saved successfully![/bold green]")
            except Exception as e:
                self.console.print(f"[bold red]Error creating save directory:[/bold red] {str(e)}")
        
        self.console.print("\nPress Enter to continue...")
        input()
    
    def help(self):
        """Display help information."""
        help_text = """
## Keyboard Shortcuts:
- `1`: Go to Scrape URL
- `2`: Go to Crawl Website
- `3`: Go to Map Website
- `4`: Go to Settings
- `5`: Show this help
- `q`: Quit the application

## About Firecrawl:
Firecrawl is an API service that takes a URL, crawls it, and converts it into clean markdown or structured data. It crawls all accessible subpages and gives you clean data for each.

## Self-hosted Instance:
You are currently using a self-hosted instance of Firecrawl. This means that all data processing happens locally on your machine.
        """
        
        self.console.print(Panel(Markdown(help_text), title="Help", box=box.ROUNDED))
        
        self.console.print("\nPress Enter to continue...")
        input()
    
    def run(self):
        """Run the application."""
        self.console.clear()
        
        while self.running:
            self.console.clear()
            self.display_header()
            self.display_welcome()
            self.display_menu()
            
            choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "q"], default="1")
            
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
            elif choice.lower() == "q":
                self.running = False
                self.console.print("[bold green]Thank you for using Firecrawl Explorer![/bold green]")
                break


def main():
    """Main entry point."""
    explorer = FirecrawlExplorer()
    explorer.run()


if __name__ == "__main__":
    main()