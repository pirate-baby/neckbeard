from pathlib import Path
from github import Github, Auth

from settings import settings

class GithubParser:
    codebase: Path

    def __init__(self):
        auth = Auth.Token(settings.github_access_token)
        self.client = Github(auth=auth)

    def get_repo(self, github_url: str):
        repo_string = "/".join(github_url.split("/")[-2:]).split(".git")[0]
        repo = self.client.get_repo(repo_string)
        return repo

    def analyze_repo(self, github_url: str):
        """gets info from github about the repo.
        predominant programming language,
        number of commits,
        oldest commit,
        newest commit,
        """
        repo = self.get_repo(github_url)
        return {
            "name": repo.name,
            "language": repo.language,
            "commits": repo.get_commits().totalCount,
            "newest_commit": repo.get_commits()[0].commit.author.date.strftime("%Y-%m-%d %H:%M:%S"),
            "oldest_commit": repo.get_commits().reversed[0].commit.author.date.strftime("%Y-%m-%d %H:%M:%S")
        }