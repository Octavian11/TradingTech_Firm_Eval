#!/usr/bin/env python3
"""
Tool Executor - Handles execution of research tools for Claude evaluations.

Implements three tools:
1. web_search: Search the web using Brave Search API
2. web_fetch: Fetch and extract content from URLs
3. file_read: Read skill files from the filesystem

This module bridges the gap between Claude's tool_use blocks and actual
research capabilities, enabling Desktop-like evaluations via API.
"""

import os
import logging
import time
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes research tools for Claude API evaluations."""

    def __init__(self, skill_base_path: str = None, brave_api_key: str = None, search_delay: float = None):
        """
        Initialize the Tool Executor.

        Args:
            skill_base_path: Base path where skill files are located.
                           Defaults to the skills directory in the project root.
            brave_api_key: Brave Search API key. If not provided, will try to load from env.
            search_delay: Delay in seconds between search requests to respect rate limits.
                         Defaults to 1.5 seconds. Can be configured via BRAVE_SEARCH_DELAY env var.
        """
        if skill_base_path is None:
            # Get project root (two levels up from this file) and point to skills directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            skill_base_path = os.path.join(project_root, "skills")
        self.skill_base_path = skill_base_path

        # Get Brave Search API key
        self.brave_api_key = brave_api_key or os.environ.get("BRAVE_SEARCH_API_KEY")
        if not self.brave_api_key:
            logger.warning("BRAVE_SEARCH_API_KEY not set - web search will fail")

        # Configure search delay for rate limiting (free tier has limits)
        if search_delay is None:
            search_delay = float(os.environ.get("BRAVE_SEARCH_DELAY", "1.5"))
        self.search_delay = search_delay
        self.last_search_time = 0  # Track last search to enforce delay

        logger.info(f"ToolExecutor initialized (search delay: {self.search_delay}s)")

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool and return its results.

        Args:
            tool_name: Name of the tool (web_search, web_fetch, file_read)
            tool_input: Input parameters for the tool

        Returns:
            String result from tool execution
        """
        logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

        try:
            if tool_name == "web_search":
                return self._web_search(tool_input.get("query", ""))
            elif tool_name == "web_fetch":
                return self._web_fetch(tool_input.get("url", ""))
            elif tool_name == "file_read":
                return self._file_read(tool_input.get("path", ""))
            else:
                error_msg = f"Unknown tool: {tool_name}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(f"{tool_name} error: {e}", exc_info=True)
            return f"Error: {error_msg}"

    def _web_search(self, query: str) -> str:
        """
        Search the web using Brave Search API.

        Args:
            query: Search query

        Returns:
            Formatted search results
        """
        if not query:
            return "Error: No search query provided"

        if not self.brave_api_key:
            return "Error: BRAVE_SEARCH_API_KEY not configured"

        # Rate limiting: enforce delay between consecutive searches
        time_since_last_search = time.time() - self.last_search_time
        if time_since_last_search < self.search_delay:
            sleep_time = self.search_delay - time_since_last_search
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s before search")
            time.sleep(sleep_time)

        try:
            # Call Brave Search API
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }
            params = {
                "q": query,
                "count": 10  # Get up to 10 results
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)
            self.last_search_time = time.time()  # Update last search time
            response.raise_for_status()

            data = response.json()
            results = data.get("web", {}).get("results", [])

            if not results:
                return f"No results found for query: {query}"

            # Format results
            formatted_results = [f"Search results for: {query}\n"]

            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                description = result.get('description', 'No description')
                url = result.get('url', 'No URL')

                formatted_results.append(
                    f"{i}. {title}\n"
                    f"   URL: {url}\n"
                    f"   {description}\n"
                )

            result_text = "\n".join(formatted_results)
            logger.info(f"web_search returned {len(results)} results for: {query}")
            return result_text

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                error_msg = f"Rate limit exceeded. Consider increasing BRAVE_SEARCH_DELAY (current: {self.search_delay}s)"
                logger.error(error_msg)
                return f"Error: {error_msg}"
            else:
                error_msg = f"Search failed: {str(e)}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
        except requests.exceptions.RequestException as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    def _web_fetch(self, url: str) -> str:
        """
        Fetch and extract text content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Extracted text content
        """
        if not url:
            return "Error: No URL provided"

        try:
            # Fetch the URL with timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML and extract text
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # Limit to first 5000 characters to avoid token issues
            if len(text) > 5000:
                text = text[:5000] + "\n\n[Content truncated at 5000 characters]"

            logger.info(f"web_fetch successfully fetched {len(text)} chars from: {url}")
            return f"Content from {url}:\n\n{text}"

        except requests.Timeout:
            error_msg = f"Timeout fetching URL: {url}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except requests.RequestException as e:
            error_msg = f"Failed to fetch URL: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Error processing content: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    def _file_read(self, path: str) -> str:
        """
        Read a file from the filesystem (skill files).

        Args:
            path: File path to read

        Returns:
            File contents
        """
        if not path:
            return "Error: No file path provided"

        try:
            # If path doesn't start with skill_base_path, prepend it
            if not path.startswith(self.skill_base_path):
                full_path = os.path.join(self.skill_base_path, path)
            else:
                full_path = path

            # Security check: ensure path is within skill base path
            real_path = os.path.realpath(full_path)
            real_base = os.path.realpath(self.skill_base_path)

            if not real_path.startswith(real_base):
                error_msg = f"Access denied: Path outside skill directory: {path}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

            # Read the file
            with open(real_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"file_read successfully read {len(content)} chars from: {path}")
            return content

        except FileNotFoundError:
            error_msg = f"File not found: {path}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except PermissionError:
            error_msg = f"Permission denied reading file: {path}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"


# Tool definitions for Claude API
TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": "Search the web for information about companies, people, funding, products, etc. Returns up to 10 search results with titles, URLs, and descriptions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'EZX Inc Westfield NJ', 'Paul Savin founder', 'EZX Inc funding investors')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "web_fetch",
        "description": "Fetch and extract text content from a specific URL. Returns the main text content of the webpage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch (e.g., 'https://www.ezxinc.com', 'https://www.linkedin.com/company/ezx-inc')"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "file_read",
        "description": "Read a file from the skill directory (e.g., skill files, reference documents, evaluation criteria).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The file path relative to the skills directory (e.g., 'company-evaluator/SKILL.md', 'company-evaluator/references/investment-criteria.md')"
                }
            },
            "required": ["path"]
        }
    }
]
