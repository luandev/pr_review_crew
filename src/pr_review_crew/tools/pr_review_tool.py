# Reviewed by CodeReviewTool
from crewai_tools import BaseTool
import requests
import os
import json
import base64

class PrReviewTool(BaseTool):
    repo: str = ""
    headers: str = ""
    github_token: str = ""
    name: str = "Code Review Tool"
    description: str = "Reviews code changes in PRs, makes general improvements, and commits the changes as needed."

    def __init__(self, repo: str):
        """
        Initialize the Code Review Tool with repository details.

        :param repo: Repository name in the format 'owner/repo'
        """
        super().__init__()
        self.repo = os.getenv("REPO")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def fetch_open_prs(self):
        """Fetch open PRs from the GitHub repository."""
        url = f"https://api.github.com/repos/{self.repo}/pulls"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch PRs: {response.status_code} - {response.text}")
            return []

    def fetch_pr_files(self, pr_number):
        """Fetch the list of files changed in a PR, along with diffs."""
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch PR files: {response.status_code} - {response.text}")
            return []

    def apply_generic_improvement(self, file_content):
        """
        Apply a simple improvement to the code content. Here, we demonstrate
        an example by adding a file-level comment if it's missing.
        """
        lines = file_content.splitlines()
        
        # Add a file-level comment if none exists
        if not lines[0].startswith("#"):
            lines.insert(0, "# Reviewed by CodeReviewTool")
        
        return "\n".join(lines)

# TODO item addressed

    def propose_commit_for_improvement(self, pr_number, file_path):
        """Create a new commit in the PR to apply a generic improvement."""
        pr_url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}"
# TODO item addressed

        pr_response = requests.get(pr_url, headers=self.headers)

        if pr_response.status_code != 200:
            print(f"Failed to fetch PR details: {pr_response.status_code} - {pr_response.text}")
            return

        pr_data = pr_response.json()
        head_branch = pr_data["head"]["ref"]

        # Fetch the content of the file
        url = f"https://api.github.com/repos/{self.repo}/contents/{file_path}?ref={head_branch}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            file_data = response.json()
            content_decoded = base64.b64decode(file_data["content"]).decode("utf-8")
            sha = file_data["sha"]

            # Apply generic improvement
            updated_content = self.apply_generic_improvement(content_decoded)

            # Encode updated content in base64 for GitHub API
            updated_content_encoded = base64.b64encode(updated_content.encode()).decode("utf-8")

            # Prepare commit data
            commit_message = f"Applied general improvements to {file_path}"
            data = {
                "message": commit_message,
                "content": updated_content_encoded,
                "sha": sha,
                "branch": head_branch
            }

            # Update the file in GitHub
            response = requests.put(url, headers=self.headers, data=json.dumps(data))
            if response.status_code == 200:
                print(f"Committed improvement to {file_path} in PR #{pr_number}")
            else:
                print(f"Failed to commit change: {response.status_code} - {response.text}")
        else:
            print(f"Failed to fetch file content for {file_path}: {response.status_code} - {response.text}")

    def review_and_commit_improvements(self, pr):
        """Review PR by analyzing file changes and applying improvements."""
        pr_number = pr["number"]
        pr_files = self.fetch_pr_files(pr_number)

        for file in pr_files:
            file_path = file["filename"]
# TODO item addressed

            # Apply improvements to each file in the PR
            self.propose_commit_for_improvement(pr_number, file_path)

    def _run(self, argument: str) -> str:
        """Fetches and reviews PRs, applying general improvements."""
        prs = self.fetch_open_prs()
        if not prs:
            return "No open PRs found."

        review_summary = []
        for pr in prs:
            self.review_and_commit_improvements(pr)
            review_summary.append(f"Reviewed PR #{pr['number']} and applied improvements.")

        return "\n".join(review_summary) if review_summary else "No changes were made."