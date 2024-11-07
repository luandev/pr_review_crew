import asyncio
from crewai import Crew, Agent, Task
from crewai_tools import SerperDevTool
from pr_review_crew.custom_tools import AddToQueueTool
from pr_review_crew.ollama_agent import OllamaAgent  # Import custom tool for adding URLs to queue



# News Links Finder Agent setup
news_links_finder_agent = OllamaAgent(
    role="News Links Finder",
    goal="Continuously find URLs for news articles",
    tools=[AddToQueueTool(), SerperDevTool()],  # Tool to add URLs to the queue
    max_iter=100,
    verbose=True
)

# Define a task that uses the agent
news_links_finder_task = Task(
    description="Find and add URLs to the queue",
    expected_output="Content from URLs added to the content queue",  # Define the expected output
    agent=news_links_finder_agent
)

# Assemble the crew
news_links_finder_crew_instance = Crew(
    agents=[news_links_finder_agent],
    tasks=[news_links_finder_task]
)

# Continuous function to kickoff news links finder crew
async def continuous_news_links_finder():
    try:
        while True:
            await news_links_finder_crew_instance.kickoff_async()
            await asyncio.sleep(2)  # Delay to simulate continuous link finding
    except asyncio.CancelledError:
        print("News links finder crew has been stopped gracefully.")

# Main execution setup
if __name__ == "__main__":
    try:
        asyncio.run(continuous_news_links_finder())
    except KeyboardInterrupt:
        print("Program interrupted, stopping news links finder crew.")
