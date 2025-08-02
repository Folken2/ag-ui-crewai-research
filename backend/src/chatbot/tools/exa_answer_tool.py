import os
from typing import Type, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from exa_py import Exa

class ExaAnswerInput(BaseModel):
    """Input schema for ExaAnswerTool."""
    query: str = Field(..., description="The question to get a direct answer for. Best for specific, factual questions.")
    include_text: Optional[bool] = Field(default=True, description="Whether to include full text content in the response.")

class ExaAnswerTool(BaseTool):
    name: str = "exa_answer"
    description: str = "Get a direct, LLM-generated answer to a question informed by Exa search results. Perfect for specific, factual questions that need quick answers."
    args_schema: Type[BaseModel] = ExaAnswerInput

    def __init__(self):
        super().__init__()
        # Initialize EXA client with API key from environment
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            raise ValueError("EXA_API_KEY environment variable is required for ExaAnswerTool")
        # Use object.__setattr__ to set attributes on Pydantic models
        object.__setattr__(self, 'exa_client', Exa(api_key=api_key))

    def _run(self, query: str, include_text: bool = True) -> str:
        """
        Get a direct answer to a question using EXA's answer endpoint.
        
        Args:
            query: The question to answer
            include_text: Whether to include full text content
            
        Returns:
            Formatted answer with citations
        """
        try:
            # Use EXA's answer endpoint for direct answers
            answer_response = self.exa_client.answer(
                query=query,
                text=include_text
            )
            
            # Format the response
            if not answer_response:
                return f"No answer found for query: '{query}'"
            
            # Build the formatted response
            formatted_response = f"Answer: {answer_response.answer}\n\n"
            
            # Add citations if available
            if hasattr(answer_response, 'citations') and answer_response.citations:
                formatted_response += "Sources:\n"
                for i, citation in enumerate(answer_response.citations, 1):
                    formatted_response += f"{i}. {citation.title}\n"
                    formatted_response += f"   URL: {citation.url}\n"
                    if hasattr(citation, 'author') and citation.author:
                        formatted_response += f"   Author: {citation.author}\n"
                    if hasattr(citation, 'publishedDate') and citation.publishedDate:
                        formatted_response += f"   Published: {citation.publishedDate}\n"
                    if hasattr(citation, 'text') and citation.text and include_text:
                        # Truncate text if too long
                        text_preview = citation.text[:200] + "..." if len(citation.text) > 200 else citation.text
                        formatted_response += f"   Preview: {text_preview}\n"
                    formatted_response += "\n"
            
            return formatted_response
            
        except Exception as e:
            return f"Error getting answer: {str(e)}"
