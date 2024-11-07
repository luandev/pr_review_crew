#!/usr/bin/env python
import logging
import warnings
import litellm
import os
from pr_review_crew.news_injest_crew import crew

os.environ['LITELLM_LOG'] = 'DEBUG'
def run():
    # Suppress specific warnings temporarily
    warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

    # Replace with your inputs, it will automatically interpolate any tasks and agents information
    inputs = {
        'topic': 'github_repo=luandev/pr_review_crew'
    }
    crew.kickoff(inputs=inputs)