from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pr_review_crew.tools.pr_review_tool import PrReviewTool  # Assuming we use this tool for all agents

@CrewBase
class PrReviewCrewCrew:
    """Crew for reviewing open PRs on a repository with multiple agents for comprehensive insights."""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    repo = "owner/repo"  # Replace with your actual GitHub repository

    # Define each agent with specific focus and tools
    @agent
    def pr_reviewer(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
            config=self.agents_config['pr_reviewer'],
            tools=[pr_review_tool],
            verbose=True
        )

    @agent
    def project_owner(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
            config=self.agents_config['project_owner'],
            tools=[pr_review_tool],
            verbose=True
        )

    @agent
    def staff_engineer(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
            config=self.agents_config['staff_engineer'],
            tools=[pr_review_tool],
            verbose=True
        )

    @agent
    def project_manager(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
            config=self.agents_config['project_manager'],
            tools=[pr_review_tool],
            verbose=True
        )

    # Define tasks that assign PR review to each agent
    @task
    def review_by_pr_reviewer(self) -> Task:
        return Task(
            config=self.tasks_config['review_prs'],
            agent=self.pr_reviewer(),
        )

    @task
    def review_by_project_owner(self) -> Task:
        return Task(
            config=self.tasks_config['review_prs'],
            agent=self.project_owner(),
        )

    @task
    def review_by_staff_engineer(self) -> Task:
        return Task(
            config=self.tasks_config['review_prs'],
            agent=self.staff_engineer(),
        )

    @task
    def review_by_project_manager(self) -> Task:
        return Task(
            config=self.tasks_config['review_prs'],
            agent=self.project_manager(),
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PrReviewCrew crew with sequential or parallel PR review tasks."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,  # Run agents' reviews in parallel for diverse feedback
            verbose=2,
        )
