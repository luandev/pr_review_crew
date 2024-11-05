# Reviewed by CodeReviewTool
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pr_review_crew.tools.pr_review_tool import PrReviewTool  # Assuming we use this tool for all agents
import os

@CrewBase
class PrReviewCrewCrew:
    """Crew for reviewing open PRs on a repository with multiple agents for comprehensive insights."""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    repo = os.getenv("REPO")  # Replace with your actual GitHub  "owner/repo"

    # Define the manager agent
    def manager(self) -> Agent:
        return Agent(
            role="Project Manager",
            goal="Efficiently manage the crew and ensure high-quality task completion",
            backstory="You're an experienced project manager, skilled in overseeing complex projects and guiding teams to success. Your role is to coordinate the efforts of the crew members, ensuring that each task is completed on time and to the highest standard.",
            allow_delegation=True,
        )


    # Define each agent with specific focus and tools
    @agent
    def pr_reviewer(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
# TODO item addressed

# TODO item addressed

            config=self.agents_config['pr_reviewer'],
# TODO item addressed

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
    def define_actions(self) -> Task:
        return Task(
            config=self.tasks_config['define_actions_task'],
            agent=self.project_manager(),
        )
    
    @task
    def execute_actions(self) -> Task:
        return Task(
            config=self.tasks_config['execute_actions_task'],
            agent=self.pr_reviewer(),
        )
    
    @task
    def summary_task(self) -> Task:
        return Task(
            config=self.tasks_config['summary_task'],
            agent=self.staff_engineer(),
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the PrReviewCrew crew with sequential or parallel PR review tasks."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.hierarchical,  # Run agents' reviews in parallel for diverse feedback
            manager_agent=self.manager(),
            verbose=2,
        )