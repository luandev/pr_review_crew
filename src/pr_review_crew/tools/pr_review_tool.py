from typing import List, Optional
from crewai_tools import tool
import requests
import json
import logging
import base64
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define REPO as a fixed constant
REPO = os.getenv("REPO")  # Replace with the actual repository path

def get_headers() -> dict:
    """
    Retrieve the GitHub headers required for API authentication.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set.")
    return {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3.diff"
    }

@tool("Fetch Changed Lines")
def fetch_changed_lines(pr_number: int, file_path: Optional[str] = None) -> str:
    """
    Fetches the changed lines in a file or an entire PR.
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}/files"
    params = {"per_page": 100}
    changed_lines = {}

    try:
        while url:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                logger.error(f"Failed to fetch PR files: {response.status_code} - {response.text}")
                return "Failed to fetch PR files."

            files = response.json()
            for file in files:
                current_file_path = file.get('filename')
                if file_path and current_file_path != file_path:
                    continue

                patch = file.get('patch')
                if not patch:
                    logger.warning(f"No patch available for file: {current_file_path}")
                    continue

                added, removed = parse_patch(patch)
                changed_lines[current_file_path] = {
                    "added_lines": added,
                    "removed_lines": removed
                }

            url = None if 'Link' not in response.headers else parse_link_header(response.headers['Link']).get('next')

        if changed_lines:
            return f"Fetched changed lines for PR #{pr_number}."
        else:
            return "No changed lines found."

    except Exception as e:
        logger.error(f"An error occurred while fetching changed lines: {str(e)}")
        return "Error occurred while fetching changed lines."

def parse_patch(patch: str) -> (List[str], List[str]):
    """
    Parses the patch text to extract added and removed lines.
    """
    added_lines = []
    removed_lines = []
    lines = patch.splitlines()
    for line in lines:
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:].strip())
        elif line.startswith('-') and not line.startswith('---'):
            removed_lines.append(line[1:].strip())
    return added_lines, removed_lines

def parse_link_header(link_header: str) -> dict:
    """
    Parses the Link header from GitHub API to get pagination URLs.
    """
    links = {}
    for part in link_header.split(','):
        section = part.strip().split(';')
        if len(section) != 2:
            continue
        url_part = section[0].strip()[1:-1]
        rel_part = section[1].strip().split('=')[1].strip('"')
        links[rel_part] = url_part
    return links

@tool("Fetch Open PRs")
def fetch_open_prs() -> str:
    """
    Fetches and lists all open PRs from the specified GitHub repository.
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{REPO}/pulls?state=open"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        prs = response.json()
        count = len(prs)
        logger.info(f"Fetched {count} open PR(s) from {REPO}.")
        return f"Fetched {count} open PR(s) from {REPO}."
    else:
        logger.error(f"Failed to fetch PRs: {response.status_code} - {response.text}")
        return "Failed to fetch open PRs."

@tool("Create Pull Request")
def create_pull_request(title: str, body: str, head: str, base: str = "main") -> str:
    """
    Creates a new pull request.
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{REPO}/pulls"
    data = {
        "title": title,
        "head": head,
        "base": base,
        "body": body
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        pr = response.json()
        logger.info(f"Pull request '{title}' created successfully: {pr['html_url']}")
        return f"Pull request '{title}' created successfully."
    else:
        logger.error(f"Failed to create pull request: {response.status_code} - {response.text}")
        return "Failed to create pull request."

@tool("Mark File as Reviewed")
def mark_file_reviewed(pr_number: int, file_path: str) -> str:
    """
    Marks a file as reviewed by the tool using GitHub's review API.
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}/comments"
    comment_body = f"✅ The file `{file_path}` has been reviewed by the PR Review Tool."
    data = {
        "body": comment_body
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code in [200, 201]:
        logger.info(f"Marked {file_path} as reviewed in PR #{pr_number}.")
        return f"Marked {file_path} as reviewed in PR #{pr_number}."
    else:
        logger.error(f"Failed to mark file as reviewed: {response.status_code} - {response.text}")
        return "Failed to mark file as reviewed."

@tool("Get PR Comments")
def get_pr_comments(pr_number: int) -> str:
    """
    Retrieves all comments on a specific PR.
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/comments"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        comments = response.json()
        count = len(comments)
        logger.info(f"Retrieved {count} comment(s) from PR #{pr_number}.")
        return f"Retrieved {count} comment(s) from PR #{pr_number}."
    else:
        logger.error(f"Failed to fetch PR comments: {response.status_code} - {response.text}")
        return "Failed to fetch PR comments."

@tool("Post Change Suggestion")
def post_change_suggestion(pr_number: int, file_path: str, suggestion: str) -> str:
    """
    Posts a suggestion for a change on a specific line of a file in a PR.
    """
    headers = get_headers()
    comment_body = f"💡 **Suggestion:** {suggestion}"
    url = f"https://api.github.com/repos/{REPO}/issues/{pr_number}/comments"
    data = {
        "body": comment_body
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code in [200, 201]:
        logger.info(f"Posted change suggestion on '{file_path}' in PR #{pr_number}.")
        return f"Posted change suggestion on '{file_path}' in PR #{pr_number}."
    else:
        logger.error(f"Failed to post change suggestion: {response.status_code} - {response.text}")
        return "Failed to post change suggestion."

@tool("Create File")
def create_file(branch_name: str, file_path: str, content: str, commit_message: str) -> str:
    """
    Creates or updates a file in the repository.
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    params = {"ref": branch_name}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        sha = response.json().get('sha')
        logger.info(f"File '{file_path}' exists. Preparing to update.")
    elif response.status_code == 404:
        sha = None
        logger.info(f"File '{file_path}' does not exist. Preparing to create.")
    else:
        logger.error(f"Failed to fetch file info: {response.status_code} - {response.text}")
        return "Failed to fetch file info."

    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    data = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch_name
    }
    if sha:
        data["sha"] = sha

    response = requests.put(url, headers=headers, data=json.dumps(data))

    if response.status_code in [200, 201]:
        logger.info(f"File '{file_path}' committed successfully on branch '{branch_name}'.")
        return f"File '{file_path}' committed successfully on branch '{branch_name}'."
    else:
        logger.error(f"Failed to create/update file: {response.status_code} - {response.text}")
        return "Failed to create/update file."

@tool("Create Branch")
def create_branch(branch_name: str, base_branch: str = "main") -> str:
    """
    Creates a new branch from the base branch in the specified GitHub repository.
    
    :param branch_name: The name of the new branch to create.
    :param base_branch: The base branch from which to create the new branch (default is "main").
    :return: A success or failure message indicating the outcome of the branch creation.
    """
    headers = get_headers()

    # Get the SHA of the base branch's latest commit
    base_branch_url = f"https://api.github.com/repos/{REPO}/git/ref/heads/{base_branch}"
    response = requests.get(base_branch_url, headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to fetch base branch: {response.status_code} - {response.text}")
        return "Failed to fetch base branch."

    base_ref = response.json()
    sha = base_ref['object']['sha']
    logger.info(f"Base branch '{base_branch}' SHA: {sha}")

    # Create new branch reference
    new_branch_url = f"https://api.github.com/repos/{REPO}/git/refs"
    data = {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    }
    response = requests.post(new_branch_url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        logger.info(f"Branch '{branch_name}' created successfully.")
        return f"Branch '{branch_name}' created successfully."
    elif response.status_code == 422 and 'Reference already exists' in response.text:
        logger.warning(f"Branch '{branch_name}' already exists.")
        return f"Branch '{branch_name}' already exists."
    else:
        logger.error(f"Failed to create branch: {response.status_code} - {response.text}")
        return "Failed to create branch."
    

    from crewai_tools import tool
import requests
import json
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define REPO as a fixed constant
REPO = "owner/repo_name"  # Replace with the actual repository path

def get_headers() -> dict:
    """
    Retrieve the GitHub headers required for API authentication.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable not set.")
    return {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

@tool("List Files in Repo")
def list_files_in_repo(branch: str = "main") -> str:
    """
    Lists all files in the specified repository and branch.

    :param branch: The branch from which to list files (default is "main").
    :return: A string message listing all files in the repository or an error message.
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{REPO}/git/trees/{branch}?recursive=1"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        files_data = response.json()
        files = [file['path'] for file in files_data.get('tree', []) if file['type'] == 'blob']
        if files:
            logger.info(f"Files in repo '{REPO}' on branch '{branch}': {files}")
            return "\n".join(files)
        else:
            return "No files found in the repository."
    else:
        logger.error(f"Failed to list files: {response.status_code} - {response.text}")
        return "Failed to list files in the repository."

@tool("Download File from Repo")
def download_file_from_repo(file_path: str, branch: str = "main") -> str:
    """
    Downloads a specific file from the repository and branch.

    :param file_path: The path of the file to download.
    :param branch: The branch from which to download the file (default is "main").
    :return: The content of the file as a string if successful, or an error message.
    """
    headers = get_headers()
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}?ref={branch}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        file_data = response.json()
        file_content = base64.b64decode(file_data['content']).decode('utf-8')
        logger.info(f"Downloaded file '{file_path}' from branch '{branch}'.")
        return file_content
    elif response.status_code == 404:
        logger.error(f"File '{file_path}' not found on branch '{branch}'.")
        return f"File '{file_path}' not found on branch '{branch}'."
    else:
        logger.error(f"Failed to download file: {response.status_code} - {response.text}")
        return "Failed to download file."
