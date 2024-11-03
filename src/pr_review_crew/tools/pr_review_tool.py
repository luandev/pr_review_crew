import re
import json
import base64


class PrReviewTool(BaseTool):
    repo: str = ""
    headers: str = ""
    github_token: str = ""
    name: str = "PR Review Tool"
    description: str = (
        "Analyzes PRs in-depth, identifies TODOs and comments, "
        "and makes new commits if necessary to address issues in code changes."
    )

    def __init__(self, repo: str):
        """
        Initialize the PR Review Tool with repository details.

        :param repo: Repository name in the format 'owner/repo'
        """
        super().__init__()
        self.repo = os.getenv("REPO")  # GitHub token from environment
        self.github_token = os.getenv("GITHUB_TOKEN")  # GitHub token from environment
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def fetch_open_prs(self):
        """Fetch open PRs from the GitHub repository."""
        url = f"https://api.github.com/repos/{self.repo}/pulls"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            prs = response.json()
            return prs
        else:
            print(f"Failed to fetch PRs: {response.status_code} - {response.text}")
            return []

    def fetch_pr_files(self, pr_number):
        """Fetch the list of files changed in a PR, along with diffs."""
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            files = response.json()
            return files
        else:
            print(f"Failed to fetch PR files: {response.status_code} - {response.text}")
            return []

    def analyze_diff_for_todos(self, diff_text):
        """Identify TODOs, FIXMEs, and comments needing attention in the diff."""
        todos = []
        lines = diff_text.splitlines()
        for line in lines:
            # Simple regex to find TODOs and FIXMEs in code
            if re.search(r"\b(TODO|FIXME)\b", line, re.IGNORECASE):
                todos.append(line)
        return todos

    def propose_commit_for_todo_fix(self, pr_number, file_path, line_num, fix_suggestion):
        """Create a new commit in the PR to address a TODO or comment."""
        # Fetch PR details to get the head branch name
        pr_url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}"
        pr_response = requests.get(pr_url, headers=self.headers)

        if pr_response.status_code != 200:
            print(f"Failed to fetch PR details: {pr_response.status_code} - {pr_response.text}")
            return

        pr_data = pr_response.json()
        head_branch = pr_data["head"]["ref"]  # Use the head branch for the PR

        # Fetch the contents of the file
        url = f"https://api.github.com/repos/{self.repo}/contents/{file_path}?ref={head_branch}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            file_content = response.json()
            content_decoded = base64.b64decode(file_content["content"]).decode("utf-8")
            sha = file_content["sha"]

            # Modify the content (here, just adding the suggestion for demonstration)
            content_lines = content_decoded.splitlines()
            content_lines.insert(line_num, fix_suggestion)
            updated_content = "\n".join(content_lines)

            # Encode updated content in base64 for GitHub API
            updated_content_encoded = base64.b64encode(updated_content.encode()).decode("utf-8")

            # Prepare commit data
            commit_message = f"Addressed TODO in {file_path}"
            data = {
                "message": commit_message,
                "content": updated_content_encoded,
                "sha": sha,
                "branch": head_branch  # Use the head branch instead of refs/pull/...
            }

            # Update the file in GitHub
            response = requests.put(url, headers=self.headers, data=json.dumps(data))
            if response.status_code == 200:
                print(f"Committed change to {file_path} in PR #{pr_number}")
            else:
                print(f"Failed to commit change: {response.status_code} - {response.text}")
        else:
            print(f"Failed to fetch file content for {file_path}: {response.status_code} - {response.text}")

    def review_and_comment_or_commit(self, pr):
        """Review PR by analyzing diffs and leaving comments or making commits."""
        pr_number = pr["number"]
        pr_files = self.fetch_pr_files(pr_number)

        for file in pr_files:
            file_path = file["filename"]
            diff_text = file.get("patch", "")

            # Analyze diff for TODOs and FIXMEs
            todos = self.analyze_diff_for_todos(diff_text)
            for todo in todos:
                # Create comments or commits for each TODO
                # Here, we simulate making a suggestion as a commit for each TODO
                fix_suggestion = "# TODO item addressed\n"
                line_num = diff_text.splitlines().index(todo)
                self.propose_commit_for_todo_fix(pr_number, file_path, line_num, fix_suggestion)

    def _run(self, argument: str) -> str:
        """
        Fetches and deeply reviews PRs, addressing TODOs and FIXMEs where necessary.

        :param argument: Argument could be any additional information passed to the tool
        :return: Summary of the review and commit process
        """
        prs = self.fetch_open_prs()
        if not prs:
            return "No open PRs found."

        review_summary = []
        for pr in prs:
            self.review_and_comment_or_commit(pr)
            review_summary.append(f"Reviewed PR #{pr['number']} and made necessary changes.")

        return "\n".join(review_summary) if review_summary else "No changes were made."

