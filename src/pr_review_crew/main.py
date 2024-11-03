#!/usr/bin/env python
from pr_review_crew.crew import PrReviewCrewCrew


def run():
    # Replace with your inputs, it will automatically interpolate any tasks and agents information
    inputs = {
        'topic': 'AI LLMs'
    }
    PrReviewCrewCrew().crew().kickoff(inputs=inputs)