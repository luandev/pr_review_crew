from crewai import Agent, Crew, Process, Task, LLM
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from langchain_openai import ChatOpenAI
from pr_review_crew.write_report_tool import SaveArticleTool
from datetime import datetime
import os

llm = LLM(
    model="ollama/llama3.2:3b", 
    base_url="http://localhost:11434"
)

repo = os.getenv("REPO")
github_token = os.getenv("GITHUB_TOKEN")
scrape_website = ScrapeWebsiteTool()
serper_dev_tool = SerperDevTool()
file_writer_tool = SaveArticleTool()
# Create a logs directory if it doesn't exist
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Generate a dynamic filename based on the current date and time
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"crew_log_{current_time}.txt"

# Combine the directory and filename
log_filepath = os.path.join(logs_dir, log_filename)

manager = Agent(
    llm=llm,
    role="senior editor and master of puppets",
    goal="guarantee that we get all found news of the day and process one by one of them into articles",
    backstory="You are a manager that will treat all your emplyees like toddlers because they need all the help they can get",
    verbose=True,
)

reporter = Agent(
    llm=llm,
    role="senior news reporter",
    goal="You willl write full reportage of the given article, using catchy and short titles, but full coverage of news",
    backstory="You are a trourough and meticulous reported",
    tools=[file_writer_tool],
    verbose=True,
)

scraper = Agent(
    llm=llm,
    role="senior browser operator",
    goal="Will go to the given web page and scrape the information you find",
    backstory="You are a sezoned experienced senior software engineer specialized in scraping web pages",
    tools=[scrape_website],
    verbose=True,
)

seeker = Agent(
    llm=llm,
    role="senior press researcher",
    goal="Will go to and find information on the web",
    backstory="You are a military grade information agent specialized in finding information on the web",
    tools=[serper_dev_tool],
    max_iter=1,
    verbose=True,
)

news_injest = Task(
    description="""Find the news of the day""",
    expected_output="files of links of news articles""",
)

news_proccess = Task(
    context=[news_injest],
    description="""Visit all the gathered news links and scrape their context""",
    expected_output="a list of all news contexts",
    agent=scraper
)

news_save = Task(
    context=[news_proccess],
    description="""write a insightfull article for each found news context""",
    expected_output="all the news digested into files",
    agent=reporter
)

crew = Crew(
    agents=[reporter, scraper, seeker],
    tasks=[news_injest],
    output_log_file=log_filepath,
    manager_agent=manager,
    process=Process.hierarchical,
    memory=True,
    verbose=True,
)
