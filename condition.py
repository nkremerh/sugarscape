import math
import random

# Mental, physical conditions
# Disorders, syndromes, injuries, infectious diseases, hereditary diseases, etc.
class Condition:
    def __init__(self, conditionID, configuration):
        self.ID = conditionID
        self.configuration = configuration
        # Configuration:
        # Effects on agent (penalties, bonuses)
        # Infectious, hereditary, dormant/recessive
        # Immune system, chronic/incurable

    # Triggering condition(s) to cause disease
    # Hereditary, hidden diseases or post-exposure incubation
    def trigger(self, agent, infector=None, condition=False):
        if condition == True:
            agent.catchDisease(self, infector)

    def __str__(self):
        return f"{self.ID}"
