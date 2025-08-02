from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel, Field
from typing import List, Optional
from crewai_tools import SerperDevTool
from ...tools import ExaSearchTool, ExaAnswerTool

# Import listeners to register event handlers
from ...listeners import real_time_listener


## TOOLS
# Configure SerperDevTool with both search and news modes for comprehensive results
serper_search_tool = SerperDevTool(search_type="search")
serper_news_tool = SerperDevTool(search_type="news")
# Configure EXA tools for enhanced web search and direct answers
exa_search_tool = ExaSearchTool()
exa_answer_tool = ExaAnswerTool()

## PYDANTIC MODELS
class SourceInfo(BaseModel):
    url: str = Field(description="The source URL")
    title: Optional[str] = Field(description="The title of the source")
    image_url: Optional[str] = Field(description="Image URL associated with the source")
    snippet: Optional[str] = Field(description="Brief snippet or description")

class ResearchResult(BaseModel):
    summary: Optional[str] = Field(description="A concise summary of the research result")
    sources: Optional[List[SourceInfo]] = Field(description="A list of sources with metadata including images")
    citations: Optional[List[str]] = Field(description="A list of citations for the sources used")
    
   
@CrewBase
class ResearchCrew:
    """Research Crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"


    @agent
    def researcher_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher_agent"],
            tools=[exa_search_tool, exa_answer_tool],
            #reasoning=True,
            verbose=True,
            inject_date=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
            output_pydantic=ResearchResult,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            usage_metrics={}            
        )
