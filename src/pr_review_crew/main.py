#!/usr/bin/env python
from pr_review_crew.crew import PrReviewCrewCrew


def run():
    # Replace with your inputs, it will automatically interpolate any tasks and agents information
    inputs = {
        'topic': 'Fix all todos and improove the code'
    }
    PrReviewCrewCrew().crew().kickoff(inputs=inputs)