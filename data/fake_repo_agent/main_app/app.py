from services.processor import run_task


def start():
    return run_task({"id": 101})
