from validator import check_valid


def run_task(data):
    if check_valid(data):
        # Calls yet another file
        from ..utils.formatter import clean_data
        return clean_data(data)
