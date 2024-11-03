from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pr_review_crew.tools.pr_review_tool import PrReviewTool  # Import the custom tool

@CrewBase
class PrReviewCrewCrew:
    """Crew for reviewing open PRs on a repository."""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    repo = "owner/repo"  # Set your GitHub repository here

    @agent
    def pr_reviewer(self) -> Agent:
        # Initialize the tool with the repository name
        pr_review_tool = PrReviewTool(repo=self.repo)

        return Agent(
            config=self.agents_config['pr_reviewer'],
            tools=[pr_review_tool],  # Attach the PR review tool to this agent
            verbose=True
        )

    @task
    def review_prs_task(self) -> Task:
        """Task to review PRs using the PR Review Tool."""
        return Task(
            config=self.tasks_config['review_prs'],
            agent=self.pr_reviewer(),
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PrReviewCrew crew for reviewing PRs."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=2,
        )
