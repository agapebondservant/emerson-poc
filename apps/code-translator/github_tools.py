##############################################################################
# Github Tool Methods
##############################################################################
import os
from ghapi.core import GhApi
import os
from urllib.parse import urlparse
import base64
from dotenv import load_dotenv
load_dotenv()

class GithubTools:

    @classmethod
    def get_git_repo_api(cls, git_repo):
        """Given a git repo, returns the GhApi connector object."""
    
        repo_owner, repo_name = urlparse(git_repo).path.split("/")[1], urlparse(git_repo).path.split("/")[2]
        
        print(f"Creating repo object for {repo_owner}/{repo_name}...")
    
        repo_api = GhApi(owner=repo_owner, repo=repo_name, token=os.environ.get("GH_TOKEN"))
    
        return repo_api

    @classmethod
    def get_repo_structure(cls, tree_sha, repo_api):
        """Fetches the flattened file structure of a GitHub repository."""
        files = []
        
        tree = repo_api.git.get_tree(tree_sha=tree_sha, recursive=1)
        
        for file_obj in tree['tree']:
            
            files.append(file_obj['path'])
            
        return files

    @classmethod
    def get_github_file_content(cls, file_path, repo_api):
        
        content = repo_api.repos.get_content(path=file_path).content
        
        content = base64.b64decode(content).decode('utf-8')
    
        return content

    @classmethod
    def get_relevant_files(cls, tree_sha, repo_api):
        
        repo_files = cls.get_repo_structure(tree_sha, repo_api)
        
        print(f"Found {len(repo_files)} total files.")
    
        return repo_files