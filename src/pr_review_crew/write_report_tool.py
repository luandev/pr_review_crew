from typing import Type
from datetime import datetime
import os
from crewai_tools import BaseTool
from pydantic import BaseModel, Field

class SaveArticleInput(BaseModel):
    """Input schema for SaveArticleTool."""
    article_text: str = Field(..., description="The full text of the news article.")
    article_title: str = Field(..., description="The title of the news article, used for the file name.")

class SaveArticleTool(BaseTool):
    name: str = "SaveArticleTool"
    description: str = "Saves news articles text into organized local folders by date."
    args_schema: Type[BaseModel] = SaveArticleInput

    def _run(self, article_text: str, article_title: str) -> str:
        # Format current date for directory structure
        date_str = datetime.now().strftime("%Y-%m-%d")  # Format as YYYY-MM-DD
        directory_path = os.path.join("research", date_str)
        
        # Ensure the directory exists
        os.makedirs(directory_path, exist_ok=True)
        
        # Construct file path
        sanitized_title = article_title.replace(" ", "_").replace("/", "-")  # Avoid issues with special characters
        file_path = os.path.join(directory_path, f"{sanitized_title}.txt")
        
        # Write the article text to the file
        with open(file_path, "w") as file:
            file.write(article_text)
        
        return f"Article saved successfully at {file_path}"
