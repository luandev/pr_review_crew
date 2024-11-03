from crewai_tools import BaseTool
import requests
import os
# TODO add more comments to facilitate understanding of code
# TODO item addressed

# TODO item addressed
# TODO item addressed


# TODO item addressed




class PrReviewTool(BaseTool):
    repo: str = ""
    github_token: str = ""
    name: str = "PR Review Tool"
    description: str = (
        "Fetches open PRs from a GitHub repository, analyzes them, and leaves comments with suggestions for improvements."
    )

    def __init__(self, repo: str):
        """
        Initialize the PR Review Tool with repository details.

        :param repo: Repository name in the format 'owner/repo'
        """
        super().__init__()
        self.repo = os.getenv("REPO")  # GitHub token from environment
        self.github_token = os.getenv("GITHUB_TOKEN")  # GitHub token from environment

    def fetch_open_prs(self):
        """Fetch open PRs from the GitHub repository."""
        url = f"https://api.github.com/repos/{self.repo}/pulls"
        headers = {"Authorization": f"token {self.github_token}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            prs = response.json()
            return prs
        else:
            print(f"Failed to fetch PRs: {response.status_code} - {response.text}")
            return []

    def analyze_pr(self, pr):
        """Perform a basic analysis on a PR."""
        comments = []
        if "fix" in pr["title"].lower() or "refactor" in pr["title"].lower():
            comments.append("Good use of descriptive title.")
        else:
            comments.append("Consider making the title more descriptive of the change.")
        
        # Additional review logic could go here

        return comments

    def leave_comment_on_pr(self, pr_number, comment):
        """Leaves a comment on a PR."""
        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {"body": comment}
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            print(f"Commented on PR #{pr_number}")
        else:
            print(f"Failed to comment on PR #{pr_number}: {response.status_code} - {response.text}")

    def _run(self, argument: str) -> str:
        """
        Fetches and reviews PRs, leaving comments as needed.

        :param argument: Argument could be any additional information passed to the tool
        :return: Summary of the review process
        """
        prs = self.fetch_open_prs()
        if not prs:
            return "No open PRs found."

        review_summary = []
        for pr in prs:
            pr_number = pr["number"]
            comments = self.analyze_pr(pr)
            for comment in comments:
                self.leave_comment_on_pr(pr_number, comment)
                review_summary.append(f"Commented on PR #{pr_number}: {comment}")

        return "\n".join(review_summary) if review_summary else "No comments were made on the PRs."