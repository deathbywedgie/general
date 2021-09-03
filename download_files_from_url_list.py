#!/usr/bin/env python3

"""
Point to a text file of URLs (one per line), and download them all in sequence
"""

import argparse
import os
import random
import re
import string
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
import requests
from pathlib import Path

DESTINATION_PATH = os.getcwd()
PRESERVE_PATHS = False


class Logger:
    __log_file_path = None
    SILENT_MODE = False
    DEBUG_MODE = False

    def __init__(self):
        self.__log_file_path = os.path.join(
            DESTINATION_PATH,
            re.sub(r'.*/', '', sys.argv[0]) + '.log'
        )
        self.session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def __print(self, msg, error=False):
        if self.SILENT_MODE:
            return
        # Workaround for zsh, since it does not automatically add a line break
        if not 'x'.endswith('\n'):
            msg += '\n'
        if error:
            sys.stderr.write(msg)
        else:
            sys.stdout.write(msg)

    def __log(self, level: str, msg: str, skip_print=False, skip_log=False):
        level = level.upper().strip() + ' ' * (5 - len(level.strip()))
        # Add session ID and log level to the message, but add it after any leading white space in case newlines are added for spacing
        log_str = re.sub(r'^(\s*)', f'\1{f"[{self.session_id}] [{level}]"}: ', msg, count=1)
        if not skip_print:
            is_error = True if level == 'ERROR' else False
            self.__print(log_str, error=is_error)
        if not skip_log:
            with open(self.__log_file_path, 'a') as f:
                f.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} {log_str.strip()}\n')

    def error(self, msg: str):
        self.__log('error', msg)

    def warn(self, msg: str):
        self.__log('warn', msg)

    def info(self, msg):
        self.__log('info', msg)

    def debug(self, msg):
        if self.DEBUG_MODE:
            self.__log('debug', msg, skip_log=True)

    def print(self, msg):
        # Print raw instead of letting self.__log add the level to the message
        self.__print(msg)
        self.__log('info', msg, skip_print=True)


def get_args():
    global DESTINATION_PATH
    global PRESERVE_PATHS

    # Range of available args and expected input
    parser = argparse.ArgumentParser(description="Download files from all URLs in a target file")

    # Inputs expected from user
    parser.add_argument("url_file", type=str, help="Path to file containing a list of URLs to download (one per line)")

    # Optional args:
    optional_args = parser.add_argument_group()
    optional_args.add_argument(
        "-d", "--destination", type=str, default=os.getcwd(),
        help="Destination directory for downloaded files (defaults to current working directory)")

    optional_args.add_argument("-s", "--sleep", type=float, help="Sleep <N> seconds between downloads")
    optional_args.add_argument("-p", "--preserve_paths", action="store_true", help="Preserve file paths from URLs")

    log_options = parser.add_mutually_exclusive_group()
    log_options.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (suppress output and progress bar, so works in the background)")
    log_options.add_argument("--debug", action="store_true", help="Enable debug logging")

    # finalize the arguments provided by user
    _args = parser.parse_args()

    Logger.SILENT_MODE = _args.quiet
    Logger.DEBUG_MODE = _args.debug
    PRESERVE_PATHS = _args.preserve_paths
    DESTINATION_PATH = _args.destination if _args.destination else os.getcwd()

    return _args


def exit_with_error(msg, logger=None):
    if not logger:
        logger = log
    logger.error(msg)
    sys.exit(1)


def fetch_url_list(file_path):
    with open(file_path, 'r') as f:
        body = f.read()
    return [u for u in re.split(r'[\r\n]+', body) if u]


def update_url_list(file_path, new_list):
    with open(file_path, 'w+') as f:
        f.write('\n'.join(new_list))
    return


class Downloader:
    temp_files = []

    def __init__(self):
        pass

    def remove_temp_file(self, file):
        while file in self.temp_files:
            del self.temp_files[self.temp_files.index(file)]

    def download_with_progress_bar(self, url, file_name=None):
        # initialize a new Logger instance so each download gets a unique session ID,
        # while all messages outside of this function continue to use the same initial logger
        log = Logger()

        dt = datetime.now()
        url_parts = urllib.parse.urlparse(url)
        if not file_name:
            file_name = urllib.parse.unquote(re.sub('.*/', '', url_parts.path)) or f'unnamed_{url_parts.netloc}_{time.time_ns()}'

        download_path = DESTINATION_PATH
        if PRESERVE_PATHS:
            original_path = urllib.parse.unquote(re.sub(r'^\s*/|/[^/]+$', '', url_parts.path or '/'))
            download_path = os.path.join(DESTINATION_PATH, original_path)

        final_file_path = os.path.join(download_path, file_name)

        # Ensure unique file name for the temp file by using the current time
        temp_file = os.path.join(DESTINATION_PATH, f'{file_name}.{time.strftime("%Y-%m-%d_%H-%M-%S")}-{dt.microsecond}.tmp')
        self.temp_files.append(temp_file)
        if os.path.exists(final_file_path):
            log.warn(f'Already exists; skipped: {url}')
            return False

        with open(temp_file, "wb") as f:
            log.info(f'\nDownloading: {file_name} [{url}]')
            response = requests.get(url, stream=True)
            total_length = response.headers.get('content-length')
            if total_length is None:  # no content length header
                f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=4096):
                    f.write(data)
                    if not log.SILENT_MODE:
                        dl += len(data)
                        done = int(80 * dl / total_length)
                        sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (80 - done)))
                        sys.stdout.flush()
                if not Logger.SILENT_MODE:
                    print()
        if not os.path.exists(download_path):
            log.debug(f'Creating subfolder(s): "{download_path}"')
            Path(download_path).mkdir(parents=True, exist_ok=True)
        log.debug(f'Renaming temp file: "{temp_file}" ==> "{final_file_path}"')
        os.rename(temp_file, final_file_path)
        self.remove_temp_file(temp_file)


log = Logger()
downloader = Downloader()


def main():
    args = get_args()
    sleep_time = args.sleep or 0
    log.debug(f'Starting at {time.strftime("%Y-%m-%d %H-%M-%S")}')
    log.debug(f'Processing URL file [{args.url_file}]')
    url_list_file = args.url_file
    links = fetch_url_list(url_list_file)
    while links:
        url = links.pop(0)
        unquoted = urllib.parse.unquote(url)
        name = re.sub(r'.*/', '', unquoted)
        download_success = downloader.download_with_progress_bar(url, name)
        update_url_list(url_list_file, links)
        if links and download_success is not False:
            # pause momentarily between downloads to go easy on the remote site
            if sleep_time:
                log.debug(f'Sleeping for {int(sleep_time) if int(sleep_time) == sleep_time else sleep_time} seconds before next download')
            time.sleep(sleep_time)

    log.info('\nDone!')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n')
        for f in downloader.temp_files:
            log.warn(f'Temp file remains and must be manually deleted: {f}')
        exit_with_error("Control-C Pressed; stopping...")
