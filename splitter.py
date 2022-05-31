#!/usr/bin/env python3
import eyed3
import pathlib
import platform
import subprocess
import sys
import os
import xml.etree.ElementTree as ET
from typing import Tuple, List, Any


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

def build_segments(filename: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Creates a list or segments representing chapter names with start and end times
        Args:
            filename (str): Path to an mp3 file
        Returns:
            Tuple(str, List(str, str)): a tuple representing end time of the file, and a list of tuples representing chapter names and thier start times
    """
    try:
        audio = eyed3.load(filename)
        text_frames = audio.tag.user_text_frames
        end_time = convert_time(audio.info.time_secs)
    except Exception as e:
        print(f"Unable to parse mp3: {e}")
        return None
    for frame in text_frames:
        try:
            xmltext = frame.text
            markers = ET.fromstring(xmltext)
            base_chapter = "invalid I hope I never have chapters like this"
            chapter_section = 0
            segments = []
            for marker in markers:
                name, start_time = parse_marker(previous_chapter=base_chapter, marker=marker)
                base_chapter = name
                segments.append((name, start_time))
        except Exception as frame_parse_error:
            print(f"[WARNING] Error parsing text frame '{frame.id}':'{frame.text}': {frame_parse_error} - Continued to next frame")
    return end_time, segments

def parse_marker(previous_chapter: str, marker: Any) -> Tuple[str, str]:
    """Parses a chapter marker into a chapter name and start time
        Args:
            marker (Any): XML Marker
        Returns:
            Tuple (str, str): Chapter name and start time in MP3
    """
    # chapters can be split into several shorter sections and end up being
    # shown like this:
    #    Chapter 1         00:00.000
    #    Chapter 1 (03:21) 03:21.507
    #    Chapter 1 (06:27) 06:27.227
    #  Use the chapter name with a counter to create:
    #    Chapter 1-00      00:00.000
    #    Chapter 1-01      03:21.507
    #    Chapter 1-02      06:27.227
    name = marker[0].text.strip()
    if not name.startswith(previous_chapter):
        chapter_section = 0
    name = f"{name}_{chapter_section:02}"
    chapter_section += 1
    start_time = marker[1].text
    # ffmpeg really doesn't like times with minute field > 60, but I've
    # found some books that have this.
    time_args = start_time.split(":")
    h = 0
    m = 0
    s = 0
    if len(time_args) == 2:
        m, s = time_args
        m = int(m)
        h = 0
    elif len(time_args) == 3:
        h, m, s = time_args
        h = int(h)
        m = int(m)
    while m > 59:
        h += 1
        m -= 60
    if h != 0:
        start_time = "{0:02}:{1:02}:{2}".format(h, m, s)

    name = name.replace(" ", "_")
    return (name, start_time)

def complete_segments(segments: List[Tuple[str, str]], final_time: str) -> List[Tuple[str, str, str]]:
    new_segments = []
    for index, segment in enumerate(segments):
        if index < len(segments) - 1:
            end_time = segments[index+1][1]
        else:
            end_time = final_time
        new_segments.append((segment[0], segment[1], end_time))
    return new_segments

def split_file(filename: str, segments: List[Tuple[str, str, str]]) -> List[str]:
    fn = pathlib.Path(filename)
    # subdir = pathlib.Path(fn.stem)
    real_path = os.path.realpath(filename)
    dir_path = os.path.dirname(real_path)
    # subdir = os.path.join(dir_path, subdir)
    # os.mkdir(subdir)
    segs = []
    for index, segment in enumerate(segments):
        segname = f"{dir_path}\\{fn.stem}_{index:03}_{ clean_filename(segment[0]) }--split{fn.suffix}"
        already_created = os.path.exists(segname)

        if not already_created:
            try:
                command = ["ffmpeg",
                           "-i",
                           "" + filename + "",
                           "-acodec",
                           "copy",
                           "-ss",
                           f"{segment[1]}",
                           "-to",
                           f"{segment[2]}",
                           f"{segname}",
                           ]
                is_win = 'Win' in platform.system()
                # ffmpeg requires an output file and so it errors when it does not
                # get one so we need to capture stderr, not stdout.
                output = subprocess.check_output(command, stderr=subprocess.STDOUT,
                                                 universal_newlines=True,
                                                 shell=is_win)

            except Exception as e:
                if not os.path.exists(segname):
                    print(f"[ERROR] Unable to create file for { segment }: ", e)
            if os.path.exists(segname):
                segs.append(segname)
                print(f"Created {segname}")
        else:
            print(f"File { segname } already exists")
            # the following can be handy for debugging ffmpeg issues
            # for line in output.splitlines():
                # print(f"Got line: {line}")
    return segs


def process_single_mp3(filename: str) -> None:
    try:
        print(f"Processing:{filename}")
        allsegs = []
        end_time, segments = build_segments(filename)
        segments = complete_segments(segments, end_time)
        segs = split_file(filename, segments)
        allsegs.extend(segs)

        with open("copyit.sh", "w") as ff:
            print("#!/bin/sh", file=ff)
            print("mkdir /media/usb0/book", file=ff)
            for seg in allsegs:
                print(f"cp {seg} /media/usb0/book/", file=ff)
    except Exception as e:
        print(f"[ERROR] error splitting { filename }: { e }")


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


def process_filepath(filename: str) -> None:
    if os.path.isfile(filename):
        process_single_mp3(filename)
    elif os.path.isdir(filename):
        mp3s = get_mp3_files_in_directory(filename)
        for mp3 in mp3s:
            process_single_mp3(mp3)


def clean_filename(filename: str) -> str:
    invalid_chars = '\\/*?"\'<>|'
    return ''.join(c for c in filename if c not in invalid_chars).replace(':', '_')


if __name__=="__main__":
    for filename in sys.argv[1:]:
        process_filepath(filename)
