from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel, Field
from typing import List, Optional
from crewai_tools import SerperDevTool, EXASearchTool
import time

# Import listeners to register event handlers
from ...listeners import real_time_listener

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

## Time
current_time = time.strftime("%Y-%m-%d %H:%M:%S")

## TOOLS
serper_tool = SerperDevTool()

## PYDANTIC MODELS
class ResearchResult(BaseModel):
    summary: Optional[str] = Field(description="A concise summary of the research result")
    sources: Optional[List[str]] = Field(description="A list of sources used to gather the information")
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
            tools=[serper_tool],
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
