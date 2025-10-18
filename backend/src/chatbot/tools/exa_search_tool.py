import os
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
            Formatted search results as a string matching SourceInfo model structure
        """
        try:
            # Limit results to 10 for API efficiency
            num_results = min(num_results, 10)
            
            # Execute search with content extraction
            search_response = self.exa_client.search_and_contents(
                query=query,
                num_results=num_results,
                use_autoprompt=True,  # Use EXA's autoprompt for better results
                type="auto",  # Use auto search type as requested - automatically chooses between keyword and neural
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
                return f"No search results found for query: '{query}'"
            
            formatted_results = []
            for i, result in enumerate(search_response.results, 1):
                # Handle case where result might be a string or different object type
                if isinstance(result, str):
                    # If result is a string, treat it as a URL
                    source_info = {
                        "url": result,
                        "title": "No title available",
                        "image_url": None,
                        "snippet": "No snippet available"
                    }
                else:
                    # Get the best snippet from highlights or text
                    snippet = "No snippet available"
                    if hasattr(result, 'highlights') and result.highlights:
                        snippet = result.highlights[0]  # Use first highlight
                    elif hasattr(result, 'text') and result.text:
                        snippet = result.text[:300] + "..." if len(result.text) > 300 else result.text
                    
                    # Format as SourceInfo structure
                    source_info = {
                        "url": getattr(result, 'url', 'No URL available'),
                        "title": getattr(result, 'title', 'No title available'),
                        "image_url": getattr(result, 'image', None),  # EXA provides image URLs
                        "snippet": snippet
                    }
                
                formatted_results.append(
                    f"{i}. SourceInfo:\n"
                    f"   url: {source_info['url']}\n"
                    f"   title: {source_info['title']}\n"
                    f"   image_url: {source_info['image_url'] or 'None'}\n"
                    f"   snippet: {source_info['snippet']}\n"
                )
            
            return f"Search results for '{query}':\n\n" + "\n".join(formatted_results)
            
        except Exception as e:
            return f"Error performing web search: {str(e)}"
