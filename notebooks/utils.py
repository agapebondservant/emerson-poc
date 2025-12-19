
import traceback

import subprocess

import lancedb

import pyarrow as pa

import pyarrow.parquet as pq

import numpy as np

import json

import os

from minio import Minio

from minio.error import S3Error

from datasets import load_dataset, Dataset, concatenate_datasets

import git

import random

import shutil

############################################################################
# Dataset Processing
#############################################################################
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
        sample["code_item"] = (f"{sample['summary_type'].replace('_', ' ').capitalize()} for file path "
                           f"'{sample['code_id']}'")

        sample["text"] = (f"File path: '{sample['code_id']}'\n"
                          f"Code:\n{sample['code']}\n"
                           f"{sample['summary_type'].replace('_', ' ').capitalize()}:\
                           n{sample['summary']}\n")
        return sample

    ds = load_dataset(dataset_name, split="train").map(update_prompt_sample)

    ds.to_json(generated_jsonl_file, orient="records", lines=True)

    return ds

############################################################################
# File Processing
#############################################################################

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

############################################################################
# LanceDB Operations
#############################################################################
def get_lancedb_connection(bucket_name: str,
                                 lancedb_db_name: str,
                                 use_https: bool = True):
    """
    Establishes an asynchronous connection to a LanceDB database hosted on S3 storage using the provided
    bucket name and database name.

    Args:
        bucket_name: The name of the S3-compatible bucket where the LanceDB database is hosted.
        lancedb_db_name: The name of the LanceDB database inside the S3 bucket.
        use_https: Whether https is used. Defaults to True.
    :return: Returns a LanceDB connection object.
    """
    db = lancedb.connect(f"s3://{bucket_name}/{lancedb_db_name}",

         storage_options={
             "endpoint_url": os.getenv("AWS_S3_ENDPOINT"),

             "aws_access_key_id": os.getenv(
                 "AWS_ACCESS_KEY_ID"),

             "aws_secret_access_key": os.getenv(
                 "AWS_SECRET_ACCESS_KEY"),

             "s3_force_path_style": "true",

             "allow_http": str(use_https),
         }
     )

    return db

def create_or_update_indexing_job(git_repo: str,
                       bucket_name: str,
                       use_https: bool = True,
                       results: str = "",
                       git_sha: str = "master"
                       ):
    """
    Creates or updates an indexing job record in the database.

    Args:
        git_repo: The git repository of the application for which the indexing
        job is created or updated.
        git_sha: The git sha of the application for which the indexing job is created or updated.
        bucket_name: The name of the S3 bucket where the indexing job database is stored.
        use_https: Boolean flag indicating whether to use HTTPS for the database connection. Defaults to True.
        results: Optional results of the indexing job to be stored in the database. Defaults to None.
    """
    try:
        print(f"Setting up index for git_repo={git_repo}...")

        db = get_lancedb_connection(bucket_name, "indexing_jobs", use_https)

        data = [
            {"git_repo": git_repo, "git_sha": git_sha, "job_results": results},
        ]

        print(f"Indexing job data: {data}")

        table = db.create_table("jobs", data=data, mode="create", exist_ok=True)

        (
            table.merge_insert("git_repo")
            .when_matched_update_all()
            .when_not_matched_insert_all()
            .execute(data)
        )

        print("Indexing complete.")

    except Exception as e:
        print(f"Error while creating/updating indexing job for {git_repo}:"
              f": {e}")

        traceback.print_exc()

def fetch_indexing_job(git_repo: str,
                       bucket_name: str,
                       use_https: bool = True,
                       git_sha: str = "master"):
    """
    Fetches an indexing job for a specified application name from the database.

    Args:
        git_repo: The git repo of the application for which the indexing job is
        being retrieved.
        git_sha: The git sha of the application for which the indexing job is being retrieved.
        bucket_name: The name of the database bucket to connect to.
        use_https: Whether to use HTTPS for the database connection. Defaults to True.
    Returns:
        The results of the indexing job as stored in the database,
        or None if the job is not found or is incomplete.
    """
    try:
        db = get_lancedb_connection(bucket_name, "indexing_jobs", use_https)

        data = [
            {"git_repo": git_repo, "git_sha": git_sha, "job_results": ""},
        ]

        table = db.create_table("jobs", data=data, mode="create", exist_ok=True)

        results = table.search().where(f"git_repo = '{git_repo}' AND "
                                       f"git_sha = '{git_sha}'").select(
            ["job_results"]).to_list()

        if results and "job_results" in results[0]:
            return results[0]["job_results"]

        else:
            print("No results found")

    except Exception as e:
        print(f"Error while fetching job for {git_repo}:"
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

    os.makedirs(f"{local_lancedb_path}/output", exist_ok=True)

    try:
        ##################################################################
        # Download the GraphRAG index files from the MinIO bucket
        # and store them locally
        ##################################################################
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

        ##################################################################
        # Initialize the local Lancedb database with the downloaded index files
        ##################################################################
        local_db = lancedb.connect(local_lancedb_path)

        db = get_lancedb_connection(bucket_name, lancedb_db_name, use_https)

        for table_name in db.table_names():

            print(f"Copying table: {table_name}")

            table = db.open_table(table_name)

            data_to_copy = table.to_pandas()

            local_db.create_table(table_name, data=data_to_copy,
                                  mode="overwrite")

            if isinstance(data_to_copy, pa.Table):

                pq.write_table(data_to_copy,
                               f"{local_lancedb_path}/output/{table_name}.parquet")

            else:
                data_to_copy.to_parquet(
                    f"{local_lancedb_path}/output/{table_name}.parquet")

        print("DB index initialization complete...")

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

def register_unique_app_name_for_repo(git_repo: str,
                                      app_name: str,
                                      git_sha: str = "master",
                                      bucket_name: str = "data",
                                      use_https: bool = True):
    """
    Registers a unique application name for a given Git repository into a specified
    database.
    Args:
        git_repo: Git repository URL or identifier to associate the app name with.
        git_sha: Git commit SHA to associate with the app name. Defaults to "master".
        app_name: Name of the application to be registered uniquely for the repository.
        bucket_name: (Optional) Database bucket used to organize records.Defaults to "data".
        use_https: (Optional) Indicates whether to use HTTPS for the database connection. Defaults to True.
    """
    try:
        db = get_lancedb_connection(bucket_name, "git_repos", use_https)

        data = [
            {"git_repo": git_repo, "git_sha": git_sha, "app_name": app_name},
        ]

        table = db.create_table("git_repo_apps", data=data, mode="create",
                                exist_ok=True)

        table.merge_insert(
            data=data,
            on="git_repo"
        ).when_matched_then_update().when_not_matched_then_insert().execute()

    except Exception as e:
        print(f"Error while registering app_name {app_name}, git_repo"
              f" {git_repo}, git_sha {git_sha}:"
              f": {e}")

        traceback.print_exc()

def get_unique_app_name_for_repo(git_repo: str,
                                 git_sha: str = "master",
                                 bucket_name: str = "data",
                                 use_https: bool = True):
    """
    Generates or retrieves a unique application name for a given Git repository
    and commit.
    Args:
        git_repo: The Git repository URL or identifier.
        git_sha: The specific commit SHA to identify the repository state,default is "master".
        bucket_name: The name of the bucket used for database connection,default is "data".
        use_https: Specifies whether to use HTTPS for the connection,default is True.
    Returns:
        The unique application name associated with the given repository
        and commit, or None of none is if found.
    """
    try:
        db = get_lancedb_connection(bucket_name, "git_repos", use_https)

        data = [
            {"git_repo": git_repo, "git_sha": git_sha},
        ]

        table = db.create_table("git_repo_apps", data=data, mode="create",
                                exist_ok=True)

        results = table.search().where(f"git_repo = '{git_repo}' AND "
                                       f"git_sha = '{git_sha}'").select(
            ["app_name"]).to_list()

        if results and "app_name" in results[0]:
            return results[0]["app_name"]

        else:
            print("No results found")

    except Exception as e:
        print(f"Error while fetching job for {git_repo}:"
              f": {e}")

        traceback.print_exc()

############################################################################
# Github Processing
#############################################################################
def get_directory_structure(repo_path,
                            git_branch='master',
                            include_extensions=('.cfm', '.cfc', '.cfml','.java')):
    """
    Constructs the directory structure representation
    of the code in this git repository.
    The output is formatted as follows:
    ---Dir 1
    ------File 1
    ------File 2
    ---Dir 2
    ------File 3
    (...etc...)

    Args:
        repo_path: The path to the Git repository containing the indexed code.
        git_branch: The branch of the Git repository to be used for indexing. Defaults to 'master'.
        include_extensions: A tuple of file extensions to be included in the directory structure.
    """
    tmpdir = f"tmp{random.randint(1, 1000)}"

    try:

        os.makedirs(tmpdir, exist_ok=True)

        repo = git.Repo.clone_from(repo_path, tmpdir, branch=git_branch)

        tree = repo.tree()

        paths = []

        print(f"Repository: {repo.working_tree_dir}\n")

        for item in tree.traverse():

            if (item.type == 'blob' and os.path.splitext(item.path)[1] in
                    include_extensions):
                paths.append(item.path)

        paths, visited, directory_structure = sorted(paths), [], []

        for path in paths:

            splits = path.split("/")

            for i in range(1, len(splits) + 1):

                prefix, subpath = splits[:i], splits[i - 1]

                if prefix not in visited:
                    visited.append(prefix)

                    directory_structure.append("---" * i + subpath)

        return "\n".join(directory_structure)

    except Exception as e:

        traceback.print_exc()

    finally:

        shutil.rmtree(tmpdir)