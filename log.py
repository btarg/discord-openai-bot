import logging

# Define the log format
log_format = (
    '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s')

# Define basic configuration
logging.basicConfig(
    # Define logging level
    level=logging.INFO,
    # Declare the object we created to format the log messages
    format=log_format,
    # Declare handlers
    handlers=[
        logging.StreamHandler()
    ]
)