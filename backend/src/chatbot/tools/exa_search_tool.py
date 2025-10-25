import os
import json
from typing import Type, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from exa_py import Exa

class ExaSearchInput(BaseModel):
    """Input schema for ExaSearchTool."""
    query: str = Field(..., description="The search query to find relevant information on the web.")
    num_results: Optional[int] = Field(default=5, description="Number of search results to return (default: 5, max: 10).")

class ExaSearchTool(BaseTool):
    name: str = "exa_web_search"
    description: str = "Search the web for current and relevant information using EXA search API. Useful for finding recent news, facts, and up-to-date information on any topic."
    args_schema: Type[BaseModel] = ExaSearchInput

    def __init__(self):
        super().__init__()
        # Initialize EXA client with API key from environment
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            raise ValueError("EXA_API_KEY environment variable is required for ExaSearchTool")
        # Use object.__setattr__ to set attributes on Pydantic models
        object.__setattr__(self, 'exa_client', Exa(api_key=api_key))

    def _run(self, query: str, num_results: int = 5) -> str:
        """
        Execute a web search using EXA API with content extraction.
        
        Args:
            query: The search query
            num_results: Number of results to return (max 10)
            
        Returns:
            JSON string containing search results in SourceInfo format for easy parsing
        """
        try:
            # Limit results to 10 for API efficiency
            num_results = min(num_results, 10)
            
            # Execute search with content extraction
            search_response = self.exa_client.search_and_contents(
                query=query,
                num_results=num_results,
                use_autoprompt=True,  # Use EXA's autoprompt for better results
                type="auto",  # Use auto search type - automatically chooses between keyword and neural
                # Extract content with highlights and summaries
                text=True,  # Get full page text
                highlights={
                    "num_sentences": 3,  # Get 3 sentences per highlight
                    "highlights_per_url": 1,  # Get 1 highlight per URL
                    "query": "Key information and main points"  # Custom query for highlights
                },
                summary={
                    "query": "Main developments and key points"  # Custom query for summary
                }
            )
            
            # Format results to match SourceInfo model structure
            if not search_response.results:
                return json.dumps({
                    "query": query,
                    "results": [],
                    "message": "No search results found"
                })
            
            # Build structured results array
            structured_results = []
            for result in search_response.results:
                # Handle case where result might be a string or different object type
                if isinstance(result, str):
                    # If result is a string, treat it as a URL
                    source_info = {
                        "url": result,
                        "title": "Unknown",
                        "image_url": None,
                        "snippet": ""
                    }
                else:
                    # Get the best snippet from highlights, summary, or text
                    snippet = ""
                    if hasattr(result, 'summary') and result.summary:
                        snippet = result.summary[:300]
                    elif hasattr(result, 'highlights') and result.highlights:
                        snippet = result.highlights[0]  # Use first highlight
                    elif hasattr(result, 'text') and result.text:
                        snippet = result.text[:300]
                    
                    # Add ellipsis if truncated
                    if snippet and len(snippet) >= 300:
                        snippet = snippet + "..."
                    
                    # Try different possible attribute names for image
                    image_url = None
                    for attr in ['image', 'image_url', 'thumbnail', 'imageUrl']:
                        if hasattr(result, attr):
                            image_url = getattr(result, attr)
                            if image_url:  # Stop at first non-null value
                                break
                    
                    # Format as SourceInfo structure with all required fields
                    source_info = {
                        "url": getattr(result, 'url', ''),
                        "title": getattr(result, 'title', 'Unknown'),
                        "image_url": image_url,  # Will be None if no image found
                        "snippet": snippet if snippet else ""
                    }
                
                structured_results.append(source_info)
            
            # Return as JSON string for easy parsing by the agent
            return json.dumps({
                "query": query,
                "num_results": len(structured_results),
                "results": structured_results
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "query": query,
                "error": str(e),
                "results": []
            })
