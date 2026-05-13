import os
from git import Repo

class Cloner:
    '''Clone the given git repo to the given folder for analysis
    '''
    def __init__(self):
        self._default_dir = os.path.join(os.getenv("LOCAL_DATA_PATH"), 'temp/git')

    def handler(self, repo_url: str):
        splitted_url = repo_url.split("/")[-1].split(".")[0]
        repo_path = os.path.join(self._default_dir, splitted_url)
        
        if os.path.exists(repo_path):
            self._check_diff(repo_url, repo_path)
            return repo_path
        
        os.makedirs(repo_path, exist_ok=True)
        repo_path = repo_path if Repo.clone_from(repo_url, repo_path) else None
        return repo_path
    
    def _check_diff(self, repo_url: str, repo_path: str):
        repo = Repo(repo_path)
        repo.remotes['origin'].fetch()

        local_branch = repo.commit("main")
        remote_branch = repo.commit("origin/main")

        diffs = local_branch.diff(remote_branch)

        if diffs:
            for diff in diffs:
                print(diff)
                
        return repo