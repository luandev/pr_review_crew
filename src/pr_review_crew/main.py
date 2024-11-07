#!/usr/bin/env python
import logging
import warnings
import asyncio
import os
from pr_review_crew.news_links_finder_crew import news_links_finder_crew
from pr_review_crew.news_reader_crew import continuous_news_reader
from pr_review_crew.article_writer_crew import continuous_article_writer

# Configure logging level
os.environ['LITELLM_LOG'] = 'DEBUG'

# Suppress specific warnings temporarily
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Async function to run the news ingestion workflow
async def run_news_ingestion_pipeline():
    await asyncio.gather(
        news_links_finder_crew(),
        continuous_news_reader(),
        continuous_article_writer()
    )

def run():
    # Initialize and run the pipeline
    print("Starting the news ingestion application...")
    asyncio.run(run_news_ingestion_pipeline())
    print("News ingestion pipeline has stopped.")

if __name__ == "__main__":
    run()
