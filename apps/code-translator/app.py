import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from agentic.crew import CodeToSummary, SummaryToSpec, SpecToCode
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool
from crewai.tools import tool
from crewai.flow.flow import Flow, listen, start
import app_utils
from app_utils import NoGraphIndexFound
from urllib.parse import urlparse
import traceback
import litellm
import os
litellm.set_verbose=True
import sys


st.set_page_config(page_title="AI Code Generation", page_icon="🧠",
                   layout="wide", initial_sidebar_state="collapsed", )


st.title("AI Legacy Code Translation - Demo")
st.markdown("<br>Translates <b>ColdFusion</b> code to <b>NodeJS</b> and "
            "<b>React.</b>", unsafe_allow_html=True)
st.markdown("---")

# Main content area
col1, col2 = st.columns(2, vertical_alignment="bottom")

# Status and output area
status_container = st.container()
output_container = st.container()

# Stacktrace
with st.sidebar:
    st.title("Stacktrace")

    output_area = st.empty()

    old_stdout = sys.stdout

    sys.stdout = app_utils.OutputRedirector(
        output_area.text)

with col1:
    git_repo = st.text_input("Git repository",
                          placeholder="https://github.com/user/repo")
    git_branch_sha = st.text_input("Git branch",
                          placeholder="main, master, etc.")

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    run_button = st.button("🚀 Run", type="primary",
                           use_container_width=True)

##############################################################################
# Flows
##############################################################################


class CodeTranslationFlow(Flow):
    """Flow for CodeTranslation."""

    @start()
    def retrieve_code_summary(self):

        git_repo = self.state["repo_url"]

        git_sha = self.state["repo_branch_sha"]

        bucket_name = os.getenv("AWS_S3_BUCKET")

        print(
            f"Starting flow {self.state['id']} for "
            f"{git_repo}#{git_sha}...")

        summary = app_utils.get_graphrag_summary(git_repo, bucket_name)

        if not summary:
            raise NoGraphIndexFound()

        self.state["summary"] = summary

    @listen(retrieve_code_summary)
    def analyze_code(self):

        summary = self.state["summary"]

        # Get spec from aggregated summary
        spec = SummaryToSpec().crew().kickoff(

            inputs={"inputs": summary,

                    "output_base_path": f"{self.state["repo_id"]}",})

        return spec.raw

    @listen(analyze_code)
    def generate_code(self, spec):

        print("Generating code!...")

        repo_id = self.state["repo_id"]

        code = SpecToCode().crew().kickoff(
            inputs={"spec": spec, "output_base_path": f"{repo_id}",
                    "code_base_path": f"{repo_id}/code",})

        return code.raw

if run_button:
    if not git_repo or not git_branch_sha:
        st.error("⚠️ Git repository and branch are required fields.")
    else:
        with status_container:

            with st.spinner("🤖 Working on it..."):
                try:

                    progress_bar = st.progress(0)

                    status_text = st.empty()

                    flow = CodeTranslationFlow()

                    flow.plot("CodeTranslationFlowPlot")

                    repo_id = ("_").join(
                        urlparse(git_repo).path.split("/")[1:])

                    status_text.text(
                        "🔍 Code Analyzer is analyzing the code information...")

                    progress_bar.progress(33)

                    result = flow.kickoff(inputs={"repo_url": git_repo,

                                                  "repo_branch_sha": git_branch_sha,

                                                  "repo_id": repo_id})

                    progress_bar.progress(100)

                    status_text.text("✅ Code translation complete.")

                    # Display the result
                    with output_container:
                        st.markdown("---")
                        st.subheader("📄 Generated Code")
                        st.markdown(result)

                        # Download button
                        st.download_button(
                            label="Download Code",
                            data=str(result),
                            file_name=f"generated_code.md",
                            mime="text/plain"
                        )

                except NoGraphIndexFound as ne:

                    status_text.text("The provided repository has not "
                                     "been indexed. Please try again with an indexed repository, "
                                     "or generate a GraphRAG index for this "
                                     "repository.")


                except Exception as e:

                    st.error(f"❌ An error occurred: {str(e)}")
                    traceback.print_exc()

# Footer
st.markdown("---")
