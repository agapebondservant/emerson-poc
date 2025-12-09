
import traceback

import subprocess

import lancedb

import pyarrow as pa

import pyarrow.parquet as pq

import json

import os

from minio import Minio

from minio.error import S3Error

from datasets import load_dataset, Dataset, concatenate_datasets

def postprocess_dataset(dataset_name: str,
                        generated_jsonl_file: str,
                        ):
    """
    Postprocesses datasets by combining prompt and baseline datasets after applying updates
    to their samples and saves the result as a JSONL file.

    Args:
        dataset_name: Name of the dataset to be processed.
        generated_jsonl_file: Path to save the processed dataset in JSONL
    Returns:
        Processed Dataset object.
    """

    def update_prompt_sample(sample):
        sample["text"] = f"{sample['summary_type']} for {sample['code_id']}"

        sample["title"] = (f"Code:\n{sample['code']}\n\n"
                           f"{sample['summary_type']}\\{sample['summary']}")
        return sample

    dataset = load_dataset(dataset_name, split="train").map(update_prompt_sample)

    dataset.to_json(generated_jsonl_file, orient="records", lines=True)

    return dataset

def split_jsonl_into_json_files(source_file: str,
                                target_dir: str):
    """
    Splits a JSONL file into individual JSON files.

    Args:
        source_file: The path to the JSONL file to be split.
        target_dir: The directory where individual JSON files will be created.
    """
    try:
        with open(source_file, 'r', encoding='utf-8') as infile:

            for idx, line in enumerate(infile):

                if line.strip():

                    item = json.loads(line.strip())

                    with (open(f"{target_dir}/{idx}.json", 'w', encoding='utf-8') as
                          outfile):

                        json.dump(item, outfile)

        print(
            f"Successfully converted '{source_file}' to json files under"
            f"'{target_dir}'.")

    except Exception as e:
        print(f"An unexpected error occurred while converting {source_file} "
              f"to json files:"
              f": {e}")

        traceback.print_exc()

def download_lancedb_index(bucket_name: str,
                           lancedb_db_name: str,
                           local_lancedb_path: str,
                           use_https: bool = True):
    """
    Downloads GraphRAG index files from a MinIO bucket and stores them to the
    specified local path.

    Args:
        bucket_name: The name of the MinIO S3 bucket containing the GraphRAG index files.
        lancedb_db_name: The prefix in the S3 bucket where the GraphRAG index files are located.
        local_lancedb_path: The local directory path where the GraphRAG index files will be downloaded and stored.
        use_https: Whether to use HTTPS for connecting to the MinIO bucket. Defaults to True.
    """
    print(f"Downloading GraphRAG index from MinIO to {local_lancedb_path}...")

    os.makedirs(local_lancedb_path, exist_ok=True)

    try:

        client = Minio(
            os.getenv("AWS_S3_ENDPOINT").removeprefix("https://").removeprefix(
                "http://"),

            access_key=os.getenv("AWS_ACCESS_KEY_ID"),

            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),

            secure=use_https
        )

        objects = client.list_objects(bucket_name, prefix=lancedb_db_name,
                                      recursive=True)

        for obj in objects:
            relative_path = os.path.relpath(obj.object_name, lancedb_db_name)

            local_file_path = os.path.join(local_lancedb_path, relative_path)

            local_subdir = os.path.dirname(local_file_path)

            os.makedirs(local_subdir, exist_ok=True)

            client.fget_object(bucket_name, obj.object_name, local_file_path)

    except Exception as e:

        print(f"An error occurred while downloading GraphRAG index: {e}")

        traceback.print_exc()

def query_lancedb_graphrag_index(prompt: str,
                root: str,
                config: str,
                response_type="JSON format",
                method: str="global"
                ):
    """
    Executes a GraphRAG query using the given parameters by invoking a subprocess.
    Args:
        prompt: The query string to be submitted to the GraphRAG tool.
        root: The root directory to be used during the query execution.
        config: The configuration file path for GraphRAG.
        response_type: The desired response format of the query. Defaults to "JSON format".
        method: The query method for the GraphRAG tool. Defaults to "global".
    Returns:
        The standard output from the subprocess as a string if successful.
    """
    try:
        result = subprocess.run(["graphrag",
                                 "query",
                                 "--root",
                                 root,
                                 "--config",
                                 config,
                                 "--method",
                                 method,
                                 "--query",
                                 prompt,
                                 "--response-type",
                                 response_type],
                                capture_output=True, text=True, check=False)

        print(f"\nSubprocess output========================================="
              f" {result.stdout}")

        if result.stderr:
            raise Exception(
                f"Error running GraphRAG query: {result.stderr}")

        return result.stdout

    except Exception as e:

        print(f"Error: {e}")

        traceback.print_exc()