#!/usr/bin/env python
from pr_review_crew.pr_creation_crew import PrCreationCrew


# def run():
#     # Replace with your inputs, it will automatically interpolate any tasks and agents information
#     inputs = {
#         'topic': 'Fix all todos and improove the code'
#     }
#     PrReviewCrewCrew().crew().kickoff(inputs=inputs)

def run():
    # Replace with your inputs, it will automatically interpolate any tasks and agents information
    inputs = {
        'topic': 'improove the code'
    }
    PrCreationCrew().crew().kickoff(inputs=inputs)