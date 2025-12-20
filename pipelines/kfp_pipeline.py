from kfp import compiler, dsl, kubernetes
from kubernetes import client
from kfp.dsl import PipelineTaskFinalStatus

from dotenv import load_dotenv
load_dotenv()

GRAPHRAG_BASE_IMAGE = ("quay.io/oawofolurh/graphrag-wb:latest")
SDGHUB_BASE_IMAGE = ("quay.io/oawofolurh/agentic:latest")

@dsl.component # Supported in KFP v2.0
def exit_op(status: PipelineTaskFinalStatus):

    print(f'Pipeline state: {status.state}')

    if status.error_message:

        print(f'Pipeline failed with error: {status.error_message}')

        raise Exception(status.error_message)

@dsl.component(
    base_image=SDGHUB_BASE_IMAGE,

    image_pull_secrets=[dsl.V1LocalObjectReference(name='quay-creds')],

    packages_to_install=[
        "datasets",
        "git+https://github.com/agapebondservant/emerson-poc/tarball/main#egg=package-1.0",
        "os"
    ]
)
def generate_code_to_text_pairs(
        git_repo: str = "https://github.com/holtonma/cf_golfap.git",
        app_name: str = "golfap"
) -> str:
    import os
    import notebooks

    hub_dataset_name = f"oaawofolu/cfcode-{app_name}"

    source_path = f'cfcode_{app_name}'

    target_path = f"cfcode_json_{app_name}"

    notebooks.clone_from_repo(git_repo, source_path)

    notebooks.generate_raw_dataset(source_path, target_path,
                         include_extensions=[".cfm", ".cfc", ".cfml"],
                         split_sections=False)

    final_dataset = notebooks.generate_synthetic_dataset(target_path)

    final_dataset.push_to_hub(hub_dataset_name)


@dsl.component(
    base_image=GRAPHRAG_BASE_IMAGE,

    image_pull_secrets=[dsl.V1LocalObjectReference(name='quay-creds')],

    packages_to_install=[
        "datasets"
    ]
)
def generate_graphrag_index(
        code_to_text_status: str
):
    pass

@dsl.pipeline(
    name="GraphRAG Code Indexing Pipeline",
    description="Generates knowledge graph for codebases using GraphRAG"
)
def code_graphrag_indexing_pipeline(
        git_repo: str,
        app_name: str
):
    dsl.get_pipeline_conf().set_image_pull_secrets([
        client.V1LocalObjectReference(name="quay-creds")
    ])

    code_to_text_step = generate_code_to_text_pairs(git_repo=git_repo,
                                                    app_name=app_name)

    graphrag_step = generate_graphrag_index(
        code_to_text_status=code_to_text_step.output)


if __name__ == "__main__":

    compiler.Compiler().compile(
        pipeline_func=code_graphrag_indexing_pipeline,

        package_path="code_graphrag_indexing_pipeline.yaml"
    )

    print("Pipeline compiled successfully to code_graphrag_indexing_pipeline.yaml.")