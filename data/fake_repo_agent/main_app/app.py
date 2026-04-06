from services.processor import run_task
from v1 import logic  # upgrade to v2


def start():
    return run_task({"id": 101})
