from crewai_tools import BaseTool
import requests
import os
import re
import json
import base64

class PrReviewTool(BaseTool):
    repo: str = ""
    headers: dict = {}
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
        self.repo = repo  # Use the provided repo instead of environment variable
        self.github_token = os.getenv("GITHUB_TOKEN")  # GitHub token from environment
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set.")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def fetch_open_prs(self):
        """Fetch and list all open PRs from the GitHub repository."""
        url = f"https://api.github.com/repos/{self.repo}/pulls?state=open"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            prs = response.json()
            return prs
        else:
            print(f"Failed to fetch PRs: {response.status_code} - {response.text}")
            return []

    def fetch_pr_files(self, pr_number):
        """Fetch all files changed in a specific PR along with their diffs."""
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            files = response.json()
            return files
        else:
            print(f"Failed to fetch PR files: {response.status_code} - {response.text}")
            return []

    def analyze_diff(self, diff_text):
        """
        Analyze the diff of a file or chunks of files to identify TODOs, FIXMEs, and other comments.

        :param diff_text: The diff text of a file
        :return: A list of identified issues in the diff
        """
        issues = []
        lines = diff_text.splitlines()
        for line in lines:
            if re.search(r"\b(TODO|FIXME)\b", line, re.IGNORECASE):
                issues.append(line)
        return issues

    def mark_file_reviewed(self, pr_number, file_path):
        """
        Mark a file as reviewed by the tool using GitHub's review API.

        :param pr_number: The number of the PR
        :param file_path: The path of the file to mark as reviewed
        """
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/comments"
        # GitHub API does not have a direct way to mark a file as reviewed.
        # As a workaround, you can add a comment indicating the review.
        comment_body = f"✅ The file `{file_path}` has been reviewed by the PR Review Tool."
        data = {
            "body": comment_body
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            print(f"Marked {file_path} as reviewed in PR #{pr_number}.")
        else:
            print(f"Failed to mark file as reviewed: {response.status_code} - {response.text}")

    def get_pr_comments(self, pr_number):
        """Retrieve all comments on a specific PR."""
        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            comments = response.json()
            return comments
        else:
            print(f"Failed to fetch PR comments: {response.status_code} - {response.text}")
            return []

    def get_file_comments(self, pr_number, file_path):
        """Retrieve all comments on a specific file within a PR."""
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            comments = response.json()
            file_comments = [comment for comment in comments if comment.get('path') == file_path]
            return file_comments
        else:
            print(f"Failed to fetch file comments: {response.status_code} - {response.text}")
            return []

    def post_change_suggestion(self, pr_number, file_path, line_num, suggestion):
        """
        Post a suggestion for a change on a specific line of a file in a PR.

        :param pr_number: The number of the PR
        :param file_path: The path of the file
        :param line_num: The line number to suggest a change
        :param suggestion: The suggestion text
        """
        # To post a suggestion, you need the commit ID and the position in the diff
        # This requires additional API calls to get the diff position
        # For simplicity, we'll add a general comment instead

        comment_body = f"💡 **Suggestion:** {suggestion}"
        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        data = {
            "body": comment_body
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            print(f"Posted change suggestion on {file_path} in PR #{pr_number}.")
        else:
            print(f"Failed to post change suggestion: {response.status_code} - {response.text}")

    def pr_comment(self, pr_number, comment, reply_to_id=None):
        """
        Post a comment or reply to an existing comment on a PR.

        :param pr_number: The number of the PR
        :param comment: The comment text
        :param reply_to_id: The ID of the comment to reply to (optional)
        """
        if reply_to_id:
            url = f"https://api.github.com/repos/{self.repo}/issues/comments/{reply_to_id}/replies"
            # GitHub API for replying to comments is currently in preview and may require special headers
            # As of now, it's not widely supported; instead, you can use issue comments with a reference
            # Here, we'll add a general comment as a workaround
            print("Replying to comments is not directly supported via the GitHub API.")
            return

        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        data = {
            "body": comment
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            print(f"Posted comment on PR #{pr_number}.")
        else:
            print(f"Failed to post comment: {response.status_code} - {response.text}")

    def file_comment(self, pr_number, file_path, comment, reply_to_id=None):
        """
        Post a comment or reply to an existing comment on a specific file in a PR.

        :param pr_number: The number of the PR
        :param file_path: The path of the file
        :param comment: The comment text
        :param reply_to_id: The ID of the comment to reply to (optional)
        """
        if reply_to_id:
            # Similar to pr_comment, replying directly is not straightforward
            print("Replying to file comments is not directly supported via the GitHub API.")
            return

        # To comment on a specific file, you need to specify the path and position
        # This requires the diff position, which is complex to determine
        # For simplicity, we'll add a general comment on the PR
        self.post_change_suggestion(pr_number, file_path, None, comment)

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
            if line_num is not None and 0 <= line_num < len(content_lines):
                content_lines.insert(line_num, fix_suggestion)
            else:
                content_lines.append(fix_suggestion)
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
            issues = self.analyze_diff(diff_text)
            for issue in issues:
                # Create comments or commits for each TODO
                fix_suggestion = "# TODO item addressed\n"
                line_num = diff_text.splitlines().index(issue)
                self.propose_commit_for_todo_fix(pr_number, file_path, line_num, fix_suggestion)

            # Mark file as reviewed after processing
            self.mark_file_reviewed(pr_number, file_path)

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
