from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pr_review_crew.tools.pr_review_tool import PrReviewTool  # Assuming we use this tool for all agents
import requests
import os

@CrewBase
class PrReviewCrewCrew:
    """Crew for reviewing open PRs on a repository with multiple agents for comprehensive insights."""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    repo = "owner/repo"  # Replace with your actual GitHub repository

# TODO item addressed

# TODO item addressed

# TODO item addressed

# TODO item addressed

# TODO item addressed

    # Define each agent with specific focus and tools
    @agent
    def pr_reviewer(self) -> Agent:
        pr_review_tool = PrReviewTool(repo=self.repo)
        return Agent(
# TODO item addressed

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
    #//TODO we need to add a agent specific for looking for areas where we could be testing to increate code coverage

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

    # Define tasks for each agent's PR review
    def review_task(self, agent):
        """Create a review task for an agent."""
        return Task(
            config=self.tasks_config['review_prs'],
            agent=agent,
        )

    @task
    def summary_task(self) -> Task:
        """Creates a summary comment on the PR with feedback from all agents."""
        
        def post_summary_comment(pr_number, summary_content):
            """Posts a summary comment on a GitHub PR."""
            url = f"https://api.github.com/repos/{self.repo}/issues/{pr_number}/comments"
            headers = {
                "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {"body": summary_content}
            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 201:
                print(f"Posted summary comment on PR #{pr_number}")
            else:
                print(f"Failed to post summary comment: {response.status_code} - {response.text}")

        def compile_feedback(pr_number):
            """Collects and compiles feedback from all agents into a single summary."""
            feedback = {
                "Senior Software Engineer": self.pr_reviewer().last_response,
                "Project Owner": self.project_owner().last_response,
                "Staff Engineer": self.staff_engineer().last_response,
                "Project Manager": self.project_manager().last_response
            }

            # Format feedback into a summary
            summary_content = "### PR Review Summary\n"
            for role, comments in feedback.items():
                summary_content += f"\n**{role} Feedback:**\n{comments}\n"

            # Post the summary comment to the PR
            post_summary_comment(pr_number, summary_content)

        # Example: assuming we run this for a specific PR number (e.g., PR #1)
        compile_feedback(pr_number=1)

        return Task(
            description="Compile and post a summary of all agent feedback on the PR.",
            task_function=compile_feedback,
            agent=self.project_owner()  # Assign one agent for task completion tracking
        )

    @crew
    def crew(self) -> Crew:
        """Creates the PrReviewCrew crew with PR review tasks and a summary task."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Ensure tasks run in sequence to collect feedback
            postprocess=self.summary_task,  # Run summary task after all other tasks
            verbose=2,
        )