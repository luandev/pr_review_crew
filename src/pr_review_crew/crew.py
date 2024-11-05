from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import GithubSearchTool
from pr_review_crew.tools.pr_review_tool import PrReviewTool
import os
from crewai_tools.tools.github_search_tool.github_search_tool import GithubSearchTool


@CrewBase
class PrReviewCrewCrew:
    repo = os.getenv("REPO")

    @agent
    def pr_reviewer(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        githubSearchTool = GithubSearchTool(
            gh_token=os.environ["GITHUB_TOKEN"],
            content_types=['code', 'repo', 'pr', 'issue']
        )

        return Agent(
            role="Senior Software Engineer",
            goal="Review PRs and provide insightful comments, and suggest improvements to the codebase.",
            backstory="\
You're a senior engineer with extensive experience in code quality and best practices. \
You provide constructive feedback on PRs, asking questions and suggesting improvements as needed.",
            tools=[pr_review_tool, githubSearchTool],
            allow_code_execution=True,
            verbose=True,
        )

    @agent
    def staff_engineer(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        githubSearchTool = GithubSearchTool(
            gh_token=os.environ["GITHUB_TOKEN"],
            content_types=['code', 'repo', 'pr', 'issue']
        )
        return Agent(
            role="Staff Engineer",
            goal="Assess architectural implications of PRs and ensure scalability, security, and reliability.",
            backstory="You're a staff engineer with deep technical expertise, responsible for upholding the \
project's architectural integrity. You review PRs for potential impact on system architecture, \
scalability, and technical debt.",
            tools=[pr_review_tool, githubSearchTool],
            verbose=True
        )

    @agent
    def project_manager(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
            role="Project Manager",
            goal="Evaluate PRs from a project management perspective, ensuring timely delivery, \
resource alignment, and risk management. Whenever all the requirements of the PR are met, \
project manager will suggest to close the PR ending the interaction",
            backstory="As the project manager, you're focused on project timelines, resource allocation, and risk. \
You assess PRs for potential impact on deadlines and coordinate necessary resources to support ongoing work.",
            tools=[pr_review_tool],
            allow_delegation=True,
            verbose=True
        )

    @task
    def analyze_repository_context(self) -> Task:
        return Task(
            description="""Build comprehensive project context:
- Read and analyze repository README
- Understand project structure and architecture
- Review contribution guidelines
- Identify key project patterns and standards
- Map dependencies and integrations""",
            expected_output="Project context report with key architectural and standard guidelines",
            agent=self.staff_engineer()
        )

    @task
    def gather_pr_information(self) -> Task:
        return Task(
            context=[self.analyze_repository_context()],
            description="""Collect and analyze all PR information:
- Fetch all open PRs from the repository
- Retrieve all comments on PRs and individual files
- Identify key changes, their purposes, and any associated issues or discussions
- Summarize the overall impact of the PRs on the project""",
            expected_output="Comprehensive report of PR changes, comments, and contextual information",
            agent=self.staff_engineer()
        )

    @task
    def review_the_code(self) -> Task:
        return Task(
            context=[self.gather_pr_information()],
            description="""Perform a detailed code review of the collected PRs:
- Analyze code changes for adherence to coding standards and best practices
- Identify any potential bugs, security vulnerabilities, or performance issues
- Ensure that the code aligns with the project's architectural guidelines
- Highlight areas of improvement and suggest refactoring where necessary""",
            expected_output="Detailed code review reports highlighting issues, suggestions, and approvals",
            agent=self.pr_reviewer()
        )

    @task
    def propose_changes(self) -> Task:
        return Task(
            context=[self.review_the_code()],
            description="""Propose necessary changes based on the code review:
- Draft comments on specific lines or sections of the PRs with improvement suggestions
- Suggest code modifications or enhancements to address identified issues
- Collaborate with the PR author to iterate on the proposed changes
- Ensure that all suggestions are constructive and align with project goals""",
            expected_output="List of proposed changes and comments submitted to the relevant PRs",
            agent=self.pr_reviewer()
        )

    @task
    def address_comments(self) -> Task:
        return Task(
            context=[self.propose_changes()],
            description="""Address existing comments and feedback on the PRs:
- Respond to comments made by reviewers or team members
- Implement changes based on feedback and update the PR accordingly
- Ensure that all discussions are resolved and that the PR meets all requirements
- Coordinate with the project manager to close PRs once all criteria are satisfied""",
            expected_output="Updated PRs with resolved comments and final approvals ready for merging",
            agent=self.pr_reviewer()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.staff_engineer(),
                self.pr_reviewer(),
                self.project_manager()
            ],
            tasks=[
                self.analyze_repository_context(),
                self.gather_pr_information(),
                self.review_the_code(),
                self.propose_changes(),
                self.address_comments()
            ],
            process=Process.sequential,
            manager_agent=self.project_manager(),
            memory=True,
            verbose=2
        )
