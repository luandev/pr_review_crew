import asyncio
from crewai import Crew, Task
from crewai_tools import ScrapeWebsiteTool
from pr_review_crew.custom_tools import RetrieveFromQueueTool, AddContentToQueueTool
from pr_review_crew.ollama_agent import OllamaAgent  # Import custom tools

# News Reader Agent setup
news_reader_agent = OllamaAgent(
    role="News Reader",
    goal="Continuously retrieve URLs, scrape website content, and add it to the content queue",
    tools=[RetrieveFromQueueTool(), AddContentToQueueTool(), ScrapeWebsiteTool()],
    max_iter=10,
    verbose=True,
)

# Task 1: Retrieve URL from Queue
news_reader_task = Task(
    description="Retrieve a URL from the queue to process.",
    expected_output="Successfully retrieved a URL from the queue.",  # Define the expected output
    agent=news_reader_agent
)

# Task 2: Scrape Website Content
news_scrape_task = Task(
    context=[news_reader_task],
    description="Scrape the content of the retrieved URL.",
    expected_output="Successfully scraped content from the URL.",  # Define the expected output
    agent=news_reader_agent
)

# Task 3: Queue Scraped Content
news_queue_task = Task(
    context=[news_scrape_task],
    description="Add the scraped content to the content queue for further processing.",
    expected_output="Successfully added the scraped content to the content queue.",  # Define the expected output
    agent=news_reader_agent
)

# Assemble the crew
news_reader_crew_instance = Crew(
    agents=[news_reader_agent],
    tasks=[news_queue_task, news_scrape_task, news_reader_task]
)

# Continuous function to kickoff news reader crew
async def continuous_news_reader():
    try:
        while True:
            await news_reader_crew_instance.kickoff_async()
            await asyncio.sleep(200)  # Delay to simulate content fetching
    except asyncio.CancelledError:
        print("News reader crew has been stopped gracefully.")

# Main execution setup
if __name__ == "__main__":
    try:
        asyncio.run(continuous_news_reader())
    except KeyboardInterrupt:
        print("Program interrupted, stopping news reader crew.")
