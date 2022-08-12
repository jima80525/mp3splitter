import os
from typing import List


class Utilities:

    @staticmethod
    def convert_time(time_secs: int) -> str:
        """Convert a number of seconds into a human-readable string representing total hours, minutes, and seconds
            Args:
                time_secs (int): count of seconds
            Returns:
                str: human readable string representing hours, minutes, and seconds
        """
        fraction = int((time_secs % 1) * 1000)
        seconds = int(time_secs)
        min, sec = divmod(seconds, 60)
        hour, min = divmod(min, 60)
        return f"{hour:02}:{min:02}:{sec:02}.{fraction:03}"

    @staticmethod
    def get_mp3_files_in_directory(directory: str) -> List[str]:
        mp3_paths = []
        files = os.listdir(directory)
        for file in files:
            if not file.endswith("--split.mp3") and file.endswith(".mp3"):
                mp3_paths.append(os.path.join(directory, file))
            else:
                fullpath = os.path.join(directory, file)
                if os.path.isdir(fullpath):
                    mp3_paths.extend(get_mp3_files_in_directory(fullpath))
        return mp3_paths

    @staticmethod
    def clean_filename(filename: str) -> str:
        invalid_chars = '\\/*?"\'<>|'
        return ''.join(c for c in filename if c not in invalid_chars).replace(':', '_')