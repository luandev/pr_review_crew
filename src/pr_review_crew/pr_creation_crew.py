from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import GithubSearchTool
from pr_review_crew.tools.pr_review_tool import create_pull_request, create_file, create_branch, post_change_suggestion, list_files_in_repo, download_file_from_repo
import os
import warnings
import logging

# Suppress specific warnings temporarily
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Set up detailed logging for debugging
logging.basicConfig(level=logging.DEBUG)

@CrewBase
class PrCreationCrew:
    repo = os.getenv("REPO")
    github_token = os.getenv("GITHUB_TOKEN")

    @agent
    def feature_ideator(self) -> Agent:
        # Tools needed: Search tool to analyze the repository state
        github_search_tool = GithubSearchTool(
            gh_token=self.github_token,
            content_types=['code', 'repo', 'pr', 'issue'],
            repo=self.repo
        )
        
        return Agent(
            role="Product Manager",
            goal="Identify and propose new features or improvements for the project.",
            backstory=(
                "You are a product manager with a keen eye for enhancing the project. "
                "Your role is to analyze the current state of the repository, identify areas "
                "for improvement, and propose actionable features or enhancements."
            ),
            tools=[github_search_tool],
            cache=True,
            verbose=True,
            max_rpm=3,
            max_iter=2
        )

    # @agent
    # def developer(self) -> Agent:
    #     # Tools needed: Tool to fetch changed lines in files/PRs and mark files as reviewed
    #     return Agent(
    #         role="Software Developer",
    #         goal="Implement the proposed features or improvements efficiently and effectively.",
    #         backstory=(
    #             "You are a skilled software developer responsible for bringing the proposed features "
    #             "to life. You ensure that the code adheres to best practices and integrates seamlessly "
    #             "with the existing codebase."
    #         ),
    #         tools=[fetch_changed_lines, mark_file_reviewed, create_file],
    #         allow_code_execution=True,
    #         cache=True,
    #         verbose=True,
    #         max_rpm=3,
    #         max_iter=2
    #     )

    @agent
    def software_developer(self) -> Agent:
        # Tools needed: Tools for PR creation and repository search
        github_search_tool = GithubSearchTool(
            gh_token=self.github_token,
            content_types=['code', 'repo', 'pr', 'issue'],
            repo=self.repo
        )
        return Agent(
            role="Software Developer",
            goal="Create and manage pull requests to integrate new features or improvements.",
            backstory=(
                "You specialize in creating and managing pull requests. Your responsibility is to ensure "
                "that PRs are well-documented, follow the project's contribution guidelines, and are "
                "ready for review by the team."
            ),
            tools=[create_pull_request, create_branch, create_file, post_change_suggestion,  list_files_in_repo, download_file_from_repo],
            cache=True,
            verbose=True,
            max_rpm=3,
            max_iter=2
        )

    @task
    def analyze_repository_context(self) -> Task:
        return Task(
            description="""Build comprehensive project context:
- Read and analyze repository files
- Understand project structure and architecture
- Review contribution guidelines
- Identify key project patterns and standards
- Map dependencies and integrations""",
            expected_output="Project context report with key architectural and standard guidelines",
            agent=self.software_developer()
        )

    @task
    def suggest_new_feature(self) -> Task:
        return Task(
            context=[self.analyze_repository_context()],
            description="""Identify and propose a new feature or improvement:
- Analyze the current project state
- Identify areas for enhancement or new features
- Provide a detailed proposal outlining the feature, its benefits, and implementation approach""",
            expected_output="Feature proposal document outlining the new feature or improvement",
            agent=self.feature_ideator()
        )

    @task
    def implement_feature(self) -> Task:
        return Task(
            context=[self.suggest_new_feature()],
            description="""Implement the proposed feature or improvement:
- Design the feature architecture
- Write the necessary code changes
- Ensure adherence to coding standards and best practices
- Write tests to cover the new functionality""",
            expected_output="Implemented feature with code changes and tests",
            agent=self.software_developer()
        )

    @task
    def create_pull_request(self) -> Task:
        return Task(
            context=[self.implement_feature()],
            description="""Create a pull request to integrate the new feature:
- Commit the implemented changes to a new branch
- Push the branch to the repository
- Open a pull request with a clear description of the changes and their purpose
- Assign appropriate reviewers""",
            expected_output="Open pull request on GitHub with the new feature implementation",
            agent=self.software_developer()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.feature_ideator(),
                self.software_developer()
            ],
            tasks=[
                self.analyze_repository_context(),
                self.suggest_new_feature(),
                self.implement_feature(),
                self.create_pull_request()
            ],
            process=Process.sequential,
            memory=True,
            verbose=2
        )
