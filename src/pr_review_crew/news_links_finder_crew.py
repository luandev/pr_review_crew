import asyncio
from datetime import datetime
from crewai import Crew, Agent, Task
from crewai_tools import SerperDevTool
from pr_review_crew.custom_tools import AddToQueueTool
from pr_review_crew.ollama_agent import OllamaAgent  # Import custom tool for adding URLs to queue

# Get today's date formatted as "YYYY-MM-DD"
today_date = datetime.now().strftime("%Y-%m-%d")

# News Links Finder Agent setup
news_links_finder_agent = OllamaAgent(
    role="News Links Finder",
    goal="Find today's news articles and add their URLs to the queue.",
    tools=[AddToQueueTool(), SerperDevTool()],
    max_iter=100,
    verbose=True
)

# Task to search for today's news articles
search_today_news_task = Task(
    description=f"Search for news articles related to today's date: {today_date}.",
    expected_output="List of news article URLs found for today.",
    agent=news_links_finder_agent
)

# Task to process search results and add URLs to the queue
add_urls_to_queue_task = Task(
    context=[search_today_news_task],
    description="Extract URLs from the search results and add them to the queue.",
    expected_output="URLs added to the queue successfully.",
    agent=news_links_finder_agent
)

# Assemble the crew
news_links_finder_crew_instance = Crew(
    memory=True,
    agents=[news_links_finder_agent],
    tasks=[search_today_news_task, add_urls_to_queue_task]
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
