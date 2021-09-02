#!/usr/bin/env python3

"""
Point to a text file of URLs (one per line), and download them all in sequence
"""

import re
import urllib.parse
import urllib.request
import os
import requests
import sys
import time
import argparse
import sys

SILENT_MODE = False
DESTINATION_PATH = os.getcwd()
TEMP_FILE = None
LOG_FILE = re.sub(r'.*/', '', sys.argv[0]) + '.log'


def get_args():
    global SILENT_MODE
    global DESTINATION_PATH

    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Download files from all URLs in a target file")

    # Inputs expected from user
    parser.add_argument("url_file", type=str, help="Path to file containing a list of URLs to download (one per line)")

    # Optional args:
    optional_args = parser.add_argument_group()
    optional_args.add_argument(
        "-d", "--destination", type=str, default=os.getcwd(),
        help="Destination directory for downloaded files (defaults to current working directory)")

    optional_args.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (suppress output and progress bar, so works in the background)")

    optional_args.add_argument("-s", "--sleep", type=float, help="Sleep <N> seconds between downloads")

    # finalize the arguments provided by user
    _args = parser.parse_args()

    SILENT_MODE = True if _args.quiet else False
    DESTINATION_PATH = _args.destination if _args.destination else os.getcwd()

    return _args


def print_error(msg):
    sys.stderr.write(re.sub(r'^(\s*)', '\1ERROR: ', msg, count=1) + '\n')


def print_warning(msg):
    if not SILENT_MODE:
        sys.stdout.write(re.sub(r'^(\s*)', '\1WARN: ', msg, count=1) + '\n')


def print_output(msg):
    if not SILENT_MODE:
        sys.stdout.write(msg + '\n')


def exit_with_error(msg):
    print_error(msg)
    sys.exit(1)


def fetch_url_list(file_path):
    with open(file_path, 'r') as f:
        body = f.read()
    return [u for u in re.split(r'[\r\n]+', body) if u]


def update_url_list(file_path, new_list):
    with open(file_path, 'w+') as f:
        f.write('\n'.join(new_list))
    return


def download_file_with_progress_bar(url, file_name):
    global TEMP_FILE
    final_target = os.path.join(DESTINATION_PATH, file_name)
    TEMP_FILE = f'{final_target}.{time.strftime("%Y-%m-%d-%H-%M-%S-%s")}.tmp'
    if os.path.exists(final_target):
        with open(os.path.join(DESTINATION_PATH, LOG_FILE), 'a') as f:
            msg = f'Already exists; skipped: {url}'
            print_warning(msg)
            f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} [INFO] {msg}\n')
        return

    with open(TEMP_FILE, "wb") as f:
        print_output(f"\nDownloading: {file_name}\n\t[ {url} ]\n")
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')
        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                f.write(data)
                if not SILENT_MODE:
                    dl += len(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50 - done)))
                    sys.stdout.flush()
    # print_output(f"Renaming...\n\tOld: {temp_file_name}\n\tNew: {file_name}")
    os.rename(TEMP_FILE, final_target)
    TEMP_FILE = None


def main():
    args = get_args()
    sleep_time = args.sleep or 0

    url_list_file = args.url_file
    links = fetch_url_list(url_list_file)
    while links:
        url = links.pop(0)
        unquoted = urllib.parse.unquote(url)
        name = re.sub(r'.*/', '', unquoted)
        download_file_with_progress_bar(url, name)
        update_url_list(url_list_file, links)
        if sleep_time and links:
            # pause momentarily between downloads to go easy on the remote site
            time.sleep(sleep_time)

    print_output('\nDone!')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n')
        if TEMP_FILE:
            print_warning(f'Temp file remains and must be manually deleted:\n\t{TEMP_FILE}')
        exit_with_error("Control-C Pressed; stopping...")
