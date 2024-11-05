from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import GithubSearchTool
from pr_review_crew.tools.pr_review_tool import PrReviewTool
import os
from crewai_tools.tools.github_search_tool.github_search_tool import GithubSearchTool



@CrewBase
class PrReviewCrewCrew:
    repo = os.getenv("REPO")

    def manager(self) -> Agent:
        return Agent(
            role="Project Manager",
            goal="Efficiently manage the crew and ensure high-quality task completion",
            backstory="You're an experienced project manager, skilled in overseeing complex projects and \
guiding teams to success. Your role is to coordinate the efforts of the crew members, \
ensuring that each task is completed on time and to the highest standard.",
            allow_delegation=True,
        )

    @agent
    def pr_reviewer(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        githubSearchTool = GithubSearchTool(gh_token=os.environ["GITHUB_TOKEN"], content_types=['code', 'repo', 'pr', 'issue']) 

        return Agent(
            role="Senior Software Engineer",
            goal="Review PRs and provide insightful comments, with specific focus on {topic}. \
I will code and remove //todo comments from the code",
            backstory="You're a senior engineer with extensive experience in code quality and best practices. \
You provide constructive feedback on PRs, asking questions and suggesting improvements as needed.",
            tools=[pr_review_tool, githubSearchTool],
            allow_code_execution=True
            verbose=True
        )

    @agent
    def project_owner(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
            role="Project Owner",
            goal="Ensure PRs align with project goals, standards, and roadmap priorities. \
I will code and add //todo comments on the code",
            backstory="As the project owner, you're focused on the big picture and overall project alignment. \
You evaluate changes based on their relevance to project objectives and whether they follow \
established project standards.",
            tools=[pr_review_tool],
            verbose=True
        )

    @agent
    def staff_engineer(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
            role="Staff Engineer",
            goal="Assess architectural implications of PRs and ensure scalability, security, and reliability.",
            backstory="You're a staff engineer with deep technical expertise, responsible for upholding the \
project's architectural integrity. You review PRs for potential impact on system architecture, \
scalability, and technical debt.",
            tools=[pr_review_tool],
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
            description="""Collect and analyze all PR information:
            - List all modified files
            - Get PR description and context
            - Identify key changes and their purpose""",
            expected_output="Comprehensive report of PR changes and context",
            agent=self.pr_reviewer()
        )

    @task
    def technical_analysis(self) -> Task:
        return Task(
            description="""""",
            expected_output="Technical analysis report with specific findings",
            agent=self.staff_engineer()
        )

    @task
    def requirements_validation(self) -> Task:
        return Task(
            description="""Validate code changes against requirements:
            - Compare changes with PR description
            - Verify alignment with project standards
            - Check architectural consistency
            - Assess impact on existing functionality""",
            expected_output="Validation report with requirements compliance status",
            agent=self.project_owner()
        )

    @task
    def review_completion_check(self) -> Task:
        return Task(
            description="""Evaluate review completeness:
            - Review all previous task outputs
            - Identify any gaps in the review
            - Determine if additional information is needed""",
            expected_output="Review status report with completion assessment",
            agent=self.project_manager()
        )

    @task
    def request_changes(self) -> Task:
        return Task(
            description="""Handle necessary change requests:
            - Compile all identified issues
            - Format clear and actionable feedback
            - Prioritize requested changes
            - Provide helpful suggestions for improvements""",
            expected_output="Formatted change requests ready for PR comments",
            agent=self.project_manager()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            process=Process.sequential,
            manager_agent=self.manager(),
            verbose=2
        )