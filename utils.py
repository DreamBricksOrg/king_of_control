import os
from datetime import datetime


def generate_timestamped_filename(base_folder: str, prefix: str, extension: str) -> str:
    """
    Generates a filename with the current timestamp in the format:
    {prefix}_YYYYMMDD_HHMMSS.{extension}

    Parameters:
    - base_folder (str): The folder where the file should be saved.
    - prefix (str): The prefix for the filename.
    - extension (str): The file extension (without the dot).

    Returns:
    - str: The full file path with the formatted filename.
    """
    # Get current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Construct the filename
    filename = f"{prefix}_{timestamp}.{extension}"

    # Return the full path
    return os.path.join(base_folder, filename)
