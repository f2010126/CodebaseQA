# logic.py
from config import ENABLE_STRICT_PROCESSING, API_TOKEN


def process_data(payload):
    """
    Processes incoming data. 
    CRITICAL: Only works if strict processing is enabled in config.py.
    """
    if not ENABLE_STRICT_PROCESSING:
        # The "Bug": It raises a generic error without explanation
        raise RuntimeError("System State Invalid")

    return f"Processed {payload} with token {API_TOKEN[:3]}..."


if __name__ == "__main__":
    # This will crash based on the current config.py
    print("This is V1 logic")
