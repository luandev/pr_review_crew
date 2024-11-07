import asyncio
from crewai import Crew, Task
from pr_review_crew.custom_tools import RetrieveContentFromQueueTool
from pr_review_crew.ollama_agent import OllamaAgent  # Import custom tool to retrieve content

# Article Writer Agent setup
article_writer_agent = OllamaAgent(
    role="Article Writer",
    goal="Generate articles based on content from queue",
    tools=[RetrieveContentFromQueueTool()],  # Tool to get content for article generation
    max_iter=100,
    verbose=True
)

# Define a task that uses the agent
article_writer_task = Task(
    description="Retrieve content and write articles",
    expected_output="Completed articles based on retrieved content",  # Define the expected output
    agent=article_writer_agent
)

# Assemble the crew
article_writer_crew_instance = Crew(
    agents=[article_writer_agent],
    tasks=[article_writer_task]
)

# Continuous function to kickoff article writer crew
async def continuous_article_writer():
    try:
        while True:
            await article_writer_crew_instance.kickoff_async()
            await asyncio.sleep(2)  # Delay to simulate article writing
    except asyncio.CancelledError:
        print("Article writer crew has been stopped gracefully.")

# Main execution setup
if __name__ == "__main__":
    try:
        asyncio.run(continuous_article_writer())
    except KeyboardInterrupt:
        print("Program interrupted, stopping article writer crew.")
