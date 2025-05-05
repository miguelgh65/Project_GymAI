# fitness_chatbot/nodes/__init__.py

# Explicitly export the progress_node function to ensure it's available for import
from fitness_chatbot.nodes.progress_node import process_progress_query
from fitness_chatbot.nodes.exercise_node import process_exercise_query
from fitness_chatbot.nodes.nutrition_node import process_nutrition_query
from fitness_chatbot.nodes.log_activity_node import log_activity
from fitness_chatbot.nodes.fitbit_node import process_fitbit_query
from fitness_chatbot.nodes.response_node import generate_final_response
from fitness_chatbot.nodes.router_node import classify_intent

# Export all functions to make them available
__all__ = [
    'process_progress_query',
    'process_exercise_query',
    'process_nutrition_query',
    'log_activity',
    'process_fitbit_query',
    'generate_final_response',
    'classify_intent'
]