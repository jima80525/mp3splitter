#!/usr/bin/env python3
import eyed3
import pathlib
import platform
import subprocess
import sys
import os
import xml.etree.ElementTree as ET

def convert_time(time_secs):
    fraction = int((time_secs % 1) * 1000)
    seconds = int(time_secs)
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return f"{hour:02}:{min:02}:{sec:02}.{fraction:03}"

def build_segments(filename):
    audio = eyed3.load(filename)
    end_time = convert_time(audio.info.time_secs)
    x = audio.tag.user_text_frames
    xmltext = x.get("OverDrive MediaMarkers").text
    markers = ET.fromstring(xmltext)
    base_chapter = "invalid I hope I never have chapters like this"
    chapter_section = 0
    segments = []
    for marker in markers:
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
        if not name.startswith(base_chapter):
            base_chapter = name
            chapter_section = 0
        name = f"{base_chapter}_{chapter_section:02}"
        chapter_section += 1
        start_time =  marker[1].text
        # ffmpeg really doesn't like times with minute field > 60, but I've
        # found some books that have this.
        m,s = start_time.split(":")
        m = int(m)
        h = 0
        while m > 59:
            h += 1
            m -= 60
        if h != 0:
            start_time = "{0:02}:{1:02}:{2}".format(h,m,s)

        name = name.replace(" ", "_")
        segments.append((name, start_time))
    return end_time, segments


def complete_segments(segments, final_time):
    new_segments = []
    for index, segment in enumerate(segments):
        if index < len(segments) - 1:
            end_time = segments[index+1][1]
        else:
            end_time = final_time
        new_segments.append((segment[0], segment[1], end_time))
    return new_segments

def split_file(filename, segments):
    fn = pathlib.Path(filename)
    # subdir = pathlib.Path(fn.stem)
    real_path = os.path.realpath(filename)
    dir_path = os.path.dirname(real_path)
    # subdir = os.path.join(dir_path, subdir)
    # os.mkdir(subdir)
    segs = []
    for index, segment in enumerate(segments):
        segname = f"{dir_path}\\{fn.stem}_{index:03}_{segment[0]}--split{fn.suffix}"
        command = ["ffmpeg",
                   "-i",
                   "" + filename + "",
                   "-acodec",
                   "copy",
                   "-ss",
                   f"{segment[1]}",
                   "-to",
                   f"{segment[2]}",
                   "" + segname + "",
                  ]

        try:
            is_win = 'Win' in platform.system()
            # ffmpeg requires an output file and so it errors when it does not
            # get one so we need to capture stderr, not stdout.
            output = subprocess.check_output(command, stderr=subprocess.STDOUT,
                                             universal_newlines=True,
                                             shell=is_win)
        except Exception as e:
            print("exception", e)
        else:
            print(f"Created {segname}")
            segs.append(segname)
            # the following can be handy for debugging ffmpeg issues
            # for line in output.splitlines():
                # print(f"Got line: {line}")
    return segs


def process_single_mp3(filename: str):
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


def get_mp3_files_in_directory(directory):
    mp3_paths = []
    files = os.listdir(directory)
    for file in files:
        if file.endswith(".mp3"):
            mp3_paths.append(os.path.join(directory, file))
        else:
            fullpath = os.path.join(directory, file)
            if os.path.isdir(fullpath):
                mp3_paths.extend(get_mp3_files_in_directory(fullpath))
    return mp3_paths


def process_filepath(filename: str):
    try:
        if os.path.isfile(filename):
            process_single_mp3(filename)
        elif os.path.isdir(filename):
            mp3s = get_mp3_files_in_directory(filename)
            for mp3 in mp3s:
                process_single_mp3(mp3)
    except Exception as e:
        print(f"oh no! {e}")


if __name__=="__main__":
    for filename in sys.argv[1:]:
        process_filepath(filename)