import os
import json
from pathlib import Path
from src.common.constants import Configuration


def read_json_file(file_directory) -> dict:
    if os.path.exists(file_directory):
        with open(file_directory, 'r') as file:
            data = json.load(file)
            return data
    return {}


def create_tmp_folder():
    Path(Configuration.PROCESSED_LINKS_CACHED_FOLDER).mkdir(parents=True, exist_ok=True)


def write_to_json(data: dict, file_path: str) -> None:
    """Write filtered words to a CSV file.

    Args:
        data(Dict): Data that needs to be saved
        file_path(str): File Path where we need to save the data
    """
    old_data = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            old_data = json.load(file)

    old_data.update(data)
    with open(file_path, 'w') as file:
        json.dump(old_data, file, indent=4)


