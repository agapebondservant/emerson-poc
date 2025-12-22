##############################################################################
# Crews
##############################################################################

from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai_tools import SerperDevTool
from crewai.tools import tool
import os


##############################################################################
# LLMs
##############################################################################

main_llm = LLM(
    
    model=f"{os.getenv('CANDIDATE_LLM_PROVIDER')}/{os.getenv('CANDIDATE_LLM_ID')}",
    
    api_key=os.getenv('CANDIDATE_LLM_TOKEN'),
    
    base_url=os.getenv('CANDIDATE_LLM_API_BASE'),

    max_tokens = 100_000,
)

@CrewBase
class CodeToSummary():
    """Generates summary for the code in a given source language"""

    agents: List[BaseAgent]
    
    tasks: List[Task]

    tasks_config = "code-to-summary/tasks.yaml"

    agents_config = "code-to-summary/agents.yaml"

    selected_model: str
        
    @agent
    def code_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['code_analyzer'],
            llm=main_llm,
        )
            
    @task
    def code_analyzer_task(self) -> Task:
        return Task(
            config=self.tasks_config["code_analyzer"], 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Code-To-Spec crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
        )

@CrewBase
class SummaryToSpec():
    """Generates spec file for the code + summary provided in a given source language"""

    agents: List[BaseAgent]
    
    tasks: List[Task]

    tasks_config = "summary-to-spec/tasks.yaml"

    agents_config = "summary-to-spec/agents.yaml"

    selected_model: str

    @agent
    def code_scribe(self) -> Agent:
        return Agent(
            config=self.agents_config['code_scribe'],
            llm=main_llm,
        )

    @task
    def code_scribe_task(self) -> Task:
        return Task(
            config=self.tasks_config["code_scribe"], 
        )

    
    @crew
    def crew(self) -> Crew:
        """Creates the Summary-to-Spec crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
        )

@CrewBase
class SpecToCode():
    """Generates code in a given target language from a spec"""

    agents: List[BaseAgent]
    
    tasks: List[Task]

    agents_config = "spec-to-code/agents.yaml"

    tasks_config = "spec-to-code/tasks.yaml"

    selected_model: str

    @agent
    def code_translator(self) -> Agent:
        return Agent(
            config=self.agents_config['code_translator'],
            llm=main_llm,
        )

    @task
    def code_translator_task(self) -> Task:
        return Task(
            config=self.tasks_config["code_translator"],
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Code Translation crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            cache=False,
        )