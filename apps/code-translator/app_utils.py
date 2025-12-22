from agentic.crew import CodeToSummary, SummaryToSpec, SpecToCode
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional
from pydantic import Field, BaseModel
from crewai_tools import SerperDevTool
from crewai.tools import tool
from crewai.flow.flow import Flow, listen, start
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from github_tools import GithubTools
load_dotenv()
from io import StringIO
import db_utils
import asyncio

##############################################################################
# Custom Exceptions
##############################################################################
class NoGraphIndexFound(Exception):
    """
    Custom exception for missing GraphRAG index.
    """
    def __init__(self, message="NO_GRAPH_INDEX_FOUND", code=None):
        self.message = message
        self.code = code
        super().__init__(self.message) # Pass the message to the base Exception class


##############################################################################
# Structured Output
##############################################################################

class FileCluster(BaseModel):
    cluster_id: int = Field(description="Cluster identifier", default=0)

    files: List[str] = Field(
        description="List of files associated with this cluster")


class GitRepo(BaseModel):
    repo_id: str = Field(description="Git repo identifier", default="0")

    repo_url: str = Field(description="Git repo URI")

    repo_branch_sha: str = Field(description="Git branch SHA")

    summary: Optional[str] = Field(
        description="Summary of the aggregated file content", default="")

    clusters: Optional[List[FileCluster]] = Field(
        description="Ranked list of file clusters ordered by number of dependencies",
        default=[])

##############################################################################
# Stacktrace Widget
##############################################################################

class OutputRedirector(StringIO):
    def __init__(self, target_st_func):
        super().__init__()
        self.target_st_func = target_st_func
        self.stream = ""

    def write(self, s):
        self.stream += s
        if "\n" in self.stream:
            self.target_st_func(self.stream)
            self.stream = ""

    def flush(self):
        if self.stream:
            self.target_st_func(self.stream)
            self.stream = ""

def get_graphrag_summary(git_repo: str,
                         bucket_name: str = "data") -> Optional[str]:
    """
    Fetches the cached GraphRag summary related to the specified Git
    repository and bucket name.
    Args:
        git_repo: The repository name or URL for which the indexing
        job details need to be fetched.
        bucket_name: The bucket name where the indexing data is stored.
        Defaults to 'data'.
    Returns: The GraphRAG generated summary of the codebase in the specified
    repository.
    """
    try:
        if os.getenv("DEV_MODE"):

            with open(f"spec/candidate.md", 'r', encoding='utf-8') as file:

                return file.read()

        return db_utils.fetch_indexing_job(git_repo, bucket_name)

    except Exception as e:

        print(f"Error while fetching GraphRAG summary for {git_repo}: {e}")

        traceback.print_exc()


##############################################################################
# GitHub Helper Functions
##############################################################################
def get_github_files(github_repo: str, tree_sha: str):
    repo_api = GithubTools.get_git_repo_api(github_repo)

    return GithubTools.get_relevant_files(tree_sha, repo_api)


def get_aggregated_github_file_content(github_repo: str,
                                       repo_files: List[str]):
    repo_api = GithubTools.get_git_repo_api(github_repo)

    output = [
        f"""============={f}\n{GithubTools.get_github_file_content(f.strip(), repo_api)}"""
        for f in repo_files]

    output = "\n".join(output)

    return output