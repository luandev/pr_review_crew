from crewai_tools import BaseTool
import requests
import os
import json
import logging
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrReviewTool(BaseTool):
    repo: str
    headers: dict
    github_token: str
    name: str = "PR Review Tool"
    description: str = (
        "Helps provide thorough code reviews, identify potential issues, and suggest improvements for PRs."
    )

    def __init__(self, repo: str):
        """
        Initialize the PR Review Tool with repository details.

        :param repo: Repository name in the format 'owner/repo'
        """
        super().__init__()
        self.repo = repo
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable not set.")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def fetch_open_prs(self) -> List[dict]:
        """Fetch and list all open PRs from the GitHub repository."""
        url = f"https://api.github.com/repos/{self.repo}/pulls?state=open"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            prs = response.json()
            logger.info(f"Fetched {len(prs)} open PR(s).")
            return prs
        else:
            logger.error(f"Failed to fetch PRs: {response.status_code} - {response.text}")
            return []

    def fetch_pr_files(self, pr_number: int) -> List[dict]:
        """Fetch all files changed in a specific PR along with their diffs."""
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/files"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            files = response.json()
            logger.info(f"Fetched {len(files)} file(s) for PR #{pr_number}.")
            return files
        else:
            logger.error(f"Failed to fetch PR files: {response.status_code} - {response.text}")
            return []

    def analyze_diff(self, pr_number: int, file_path: Optional[str] = None) -> List[str]:
        """
        Retrieve all changed lines in a PR or a specific file in diff format.

        :param pr_number: The number of the PR
        :param file_path: The path of the file (optional). If None, retrieves changed lines for all files in the PR.
        :return: A list of changed lines prefixed with '+' (added) or '-' (removed)
        """
        changed_lines = []

        if file_path:
            logger.info(f"Retrieving changed lines for file '{file_path}' in PR #{pr_number}.")
            files = self.fetch_pr_files(pr_number)
            file = next((f for f in files if f['filename'] == file_path), None)
            if not file:
                logger.error(f"File '{file_path}' not found in PR #{pr_number}.")
                return changed_lines
            diff_text = file.get('patch', '')
            if not diff_text:
                logger.warning(f"No changes detected in file '{file_path}' for PR #{pr_number}.")
                return changed_lines
            changed_lines = self._extract_changed_lines(diff_text)
        else:
            logger.info(f"Retrieving all changed lines in PR #{pr_number}.")
            files = self.fetch_pr_files(pr_number)
            for file in files:
                diff_text = file.get('patch', '')
                if not diff_text:
                    logger.info(f"No changes detected in file '{file.get('filename')}' for PR #{pr_number}.")
                    continue
                file_changed_lines = self._extract_changed_lines(diff_text)
                changed_lines.extend(file_changed_lines)

        logger.debug(f"Total changed lines retrieved: {len(changed_lines)}")
        return changed_lines

    def _extract_changed_lines(self, diff_text: str) -> List[str]:
        """
        Helper method to extract changed lines from diff text.

        :param diff_text: The diff text of a file
        :return: A list of changed lines prefixed with '+' (added) or '-' (removed)
        """
        changed = []
        for line in diff_text.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                changed.append(line)
            elif line.startswith('-') and not line.startswith('---'):
                changed.append(line)
        logger.debug(f"Extracted {len(changed)} changed lines from diff.")
        return changed

    def mark_file_reviewed(self, pr_number: int, file_path: str):
        """
        Mark a file as reviewed by the tool using GitHub's review API.

        :param pr_number: The number of the PR
        :param file_path: The path of the file to mark as reviewed
        """
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/comments"
        comment_body = f"✅ The file `{file_path}` has been reviewed by the PR Review Tool."
        data = {
            "body": comment_body
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            logger.info(f"Marked '{file_path}' as reviewed in PR #{pr_number}.")
        else:
            logger.error(f"Failed to mark file as reviewed: {response.status_code} - {response.text}")

    def get_pr_comments(self, pr_number: int) -> List[dict]:
        """Retrieve all comments on a specific PR."""
        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            comments = response.json()
            logger.info(f"Fetched {len(comments)} comment(s) for PR #{pr_number}.")
            return comments
        else:
            logger.error(f"Failed to fetch PR comments: {response.status_code} - {response.text}")
            return []

    def get_file_comments(self, pr_number: int, file_path: str) -> List[dict]:
        """Retrieve all comments on a specific file within a PR."""
        url = f"https://api.github.com/repos/{self.repo}/pulls/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            comments = response.json()
            file_comments = [comment for comment in comments if comment.get('path') == file_path]
            logger.info(f"Fetched {len(file_comments)} comment(s) for file '{file_path}' in PR #{pr_number}.")
            return file_comments
        else:
            logger.error(f"Failed to fetch file comments: {response.status_code} - {response.text}")
            return []

    def post_change_suggestion(self, pr_number: int, file_path: str, line_num: Optional[int], suggestion: str):
        """
        Post a suggestion for a change on a specific line of a file in a PR.

        :param pr_number: The number of the PR
        :param file_path: The path of the file
        :param line_num: The line number to suggest a change (optional)
        :param suggestion: The suggestion text
        """
        comment_body = f"💡 **Suggestion:** {suggestion}"
        if line_num:
            comment_body += f" (Line {line_num})"

        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        data = {
            "body": comment_body
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            logger.info(f"Posted change suggestion on '{file_path}' in PR #{pr_number}.")
        else:
            logger.error(f"Failed to post change suggestion: {response.status_code} - {response.text}")

    def pr_comment(self, pr_number: int, comment: str, reply_to_id: Optional[int] = None):
        """
        Post a comment or reply to an existing comment on a PR.

        :param pr_number: The number of the PR
        :param comment: The comment text
        :param reply_to_id: The ID of the comment to reply to (optional)
        """
        if reply_to_id:
            # GitHub API does not support direct replies to comments via the standard API.
            # A workaround is to reference the parent comment in the reply.
            comment_body = f"Reply to comment ID {reply_to_id}: {comment}"
        else:
            comment_body = comment

        url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
        data = {
            "body": comment_body
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            logger.info(f"Posted comment on PR #{pr_number}.")
        else:
            logger.error(f"Failed to post comment: {response.status_code} - {response.text}")

    def file_comment(self, pr_number: int, file_path: str, comment: str, reply_to_id: Optional[int] = None):
        """
        Post a comment or reply to an existing comment on a specific file in a PR.

        :param pr_number: The number of the PR
        :param file_path: The path of the file
        :param comment: The comment text
        :param reply_to_id: The ID of the comment to reply to (optional)
        """
        if reply_to_id:
            # Similar to pr_comment, direct replies are not supported.
            comment_body = f"Reply to comment ID {reply_to_id}: {comment}"
        else:
            comment_body = comment

        # To comment on a specific file and line, you would need the position or commit ID.
        # This requires additional API calls and is more complex.
        # For simplicity, we'll add a general comment referencing the file.

        suggestion = f"{comment} (File: `{file_path}`)"
        self.post_change_suggestion(pr_number, file_path, None, suggestion)

    def review_and_comment_or_commit(self, pr: dict):
        """
        Review a single PR, retrieve changed lines, and post comments or suggestions.

        :param pr: The PR data as a dictionary
        """
        pr_number = pr['number']
        pr_title = pr.get('title', 'No Title')
        pr_body = pr.get('body', '')
        logger.info(f"Reviewing PR #{pr_number}: {pr_title}")

        changed_lines = self.analyze_diff(pr_number)

        if not changed_lines:
            logger.warning(f"No changed lines to review for PR #{pr_number}.")
            return

        for line in changed_lines:
            if line.startswith('+'):
                # Example: Handle added lines
                suggestion = f"Consider reviewing the addition: {line[1:].strip()}"
                self.post_change_suggestion(pr_number, None, None, suggestion)
            elif line.startswith('-'):
                # Example: Handle removed lines
                suggestion = f"Consider reviewing the removal: {line[1:].strip()}"
                self.post_change_suggestion(pr_number, None, None, suggestion)

        # Optionally, mark the entire PR as reviewed
        self.mark_file_reviewed(pr_number, "All files")

        logger.info(f"Completed review for PR #{pr_number}.")

    def _run(self, argument: str) -> str:
        """
        Execute the PR review process.

        :param argument: Argument could be any additional information passed to the tool
        :return: Summary of the review process
        """
        prs = self.fetch_open_prs()
        if not prs:
            return "No open PRs found."

        review_summary = []
        for pr in prs:
            try:
                self.review_and_comment_or_commit(pr)
                review_summary.append(f"Reviewed PR #{pr['number']} - {pr.get('title', 'No Title')}.")
            except Exception as e:
                logger.error(f"Error reviewing PR #{pr['number']}: {str(e)}")
                review_summary.append(f"Failed to review PR #{pr['number']}.")
        
        return "\n".join(review_summary) if review_summary else "No changes were made."
