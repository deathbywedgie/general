#!/usr/bin/env python3

"""
Point to a text file of URLs (one per line), and download them all in sequence

Optionally: also provide a target folder for downloads
"""

import re
import urllib.parse
import urllib.request
import os
import requests
import sys
import time
import argparse

SILENT_MODE = False


def get_args():
    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Download files from all URLs in a target file")

    # Inputs expected from user
    parser.add_argument("url_file", type=str, help="Path to file containing a list of URLs to download (one per line)")

    # Optional args:
    optional_args = parser.add_argument_group()
    optional_args.add_argument(
        "-d", "--destination", type=str, default=os.getcwd(),
        help="Optional: destination directory for downloaded files (defaults to current working directory)")

    optional_args.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (no progress bar, so works in the background)")

    # finalize the arguments provided by user
    _args = parser.parse_args()

    if _args.quiet:
        global SILENT_MODE
        SILENT_MODE = True

    return _args


def print_error(msg):
    # print("ERROR: " + msg, file=sys.stderr)
    sys.stderr.write("ERROR: " + msg)


def print_output(msg):
    # print(msg, file=sys.stdout)
    sys.stdout.write(msg)


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


def download_file_with_progress_bar(url, file_name, destination_path):
    temp_file_name = file_name + '.tmp'
    temp_target = temp_file_name
    final_target = file_name
    if destination_path:
        temp_target = os.path.join(destination_path, temp_file_name)
        final_target = os.path.join(destination_path, file_name)
    with open(temp_target, "wb") as f:
        print_output(f"\nDownloading: {temp_file_name}\n\t[ {url} ]")
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
    print_output(f"Renaming...\n\tOld: {temp_file_name}\n\tNew: {file_name}")
    os.rename(temp_target, final_target)


def main():
    args = get_args()

    url_list_file = args.url_file
    links = fetch_url_list(url_list_file)
    while links:
        url = links.pop(0)
        unquoted = urllib.parse.unquote(url)
        name = re.sub(r'.*/', '', unquoted)
        download_file_with_progress_bar(url, name, destination_path=args.destination or os.getcwd())
        update_url_list(url_list_file, links)
        if links:
            # pause momentarily between downloads to go easy on the remote site
            time.sleep(2)

    print_output('\nDone!')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit_with_error("Control-C Pressed; stopping...")
