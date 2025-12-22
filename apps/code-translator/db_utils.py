import traceback

import pandas as pd

import lancedb

import os

from minio import Minio

from minio.error import S3Error

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