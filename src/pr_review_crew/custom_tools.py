import os
from typing import Type
from queue import Queue
from crewai_tools import BaseTool
from pydantic import BaseModel, Field

# Initialize queues
news_links_queue = Queue()
news_content_queue = Queue()

# Define file paths
BASE_DIR = "news_queues"
URLS_DIR = os.path.join(BASE_DIR, "urls")
CONTENT_DIR = os.path.join(BASE_DIR, "content")

# Create directories if they don't exist
os.makedirs(URLS_DIR, exist_ok=True)
os.makedirs(CONTENT_DIR, exist_ok=True)

# Load existing URLs from files into the queue
def load_urls():
    for filename in os.listdir(URLS_DIR):
        with open(os.path.join(URLS_DIR, filename), 'r') as file:
            url = file.read().strip()
            news_links_queue.put(url)

# Load existing content from files into the queue
def load_content():
    for filename in os.listdir(CONTENT_DIR):
        with open(os.path.join(CONTENT_DIR, filename), 'r') as file:
            content = file.read().strip()
            news_content_queue.put(content)

# Tool to add URLs to the news links queue
class AddToQueueInput(BaseModel):
    url: str = Field(..., description="URL to add to the queue.")

class AddToQueueTool(BaseTool):
    name: str = "AddToQueueTool"
    description: str = "Adds a URL to the news links queue."
    args_schema: Type[BaseModel] = AddToQueueInput

    def _run(self, url: str) -> str:
        # Save URL to a file
        filename = f"url_{len(os.listdir(URLS_DIR)) + 1}.txt"  # Generate unique filename
        with open(os.path.join(URLS_DIR, filename), 'w') as file:
            file.write(url)
        news_links_queue.put(url)
        return f"URL {url} added to news_links_queue."

# Empty schema for retrieval tools
class EmptyInput(BaseModel):
    pass

# Tool to retrieve URLs from the news links queue
class RetrieveFromQueueTool(BaseTool):
    name: str = "RetrieveFromQueueTool"
    description: str = "Retrieves the next URL from the news links queue."
    args_schema: Type[BaseModel] = EmptyInput

    def _run(self) -> str:
        if not news_links_queue.empty():
            url = news_links_queue.get()
            return f"Retrieved URL: {url}"
        else:
            return "news_links_queue is empty."

# Tool to add content to the news content queue
class AddContentToQueueInput(BaseModel):
    content: str = Field(..., description="Content to add to the queue.")

class AddContentToQueueTool(BaseTool):
    name: str = "AddContentToQueueTool"
    description: str = "Adds article content to the news content queue."
    args_schema: Type[BaseModel] = AddContentToQueueInput

    def _run(self, content: str) -> str:
        # Save content to a file
        filename = f"content_{len(os.listdir(CONTENT_DIR)) + 1}.txt"  # Generate unique filename
        with open(os.path.join(CONTENT_DIR, filename), 'w') as file:
            file.write(content)
        news_content_queue.put(content)
        return "Content added to news_content_queue."

# Tool to retrieve content from the news content queue
class RetrieveContentFromQueueTool(BaseTool):
    name: str = "RetrieveContentFromQueueTool"
    description: str = "Retrieves the next piece of content from the news content queue."
    args_schema: Type[BaseModel] = EmptyInput

    def _run(self) -> str:
        if not news_content_queue.empty():
            content = news_content_queue.get()
            return f"Retrieved content: {content}"
        else:
            return "news_content_queue is empty."

# Load the queues on startup
load_urls()
load_content()
