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
import concurrent.futures
from clint.textui import progress

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
    optional_args.add_argument("-t", "--threads", type=int, default=1, help="Thread count for multithreading (default: 1)")

    log_options = parser.add_mutually_exclusive_group()
    log_options.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (suppress output and progress bar, so works in the background)")
    log_options.add_argument("--debug", action="store_true", help="Enable debug logging")

    # finalize the arguments provided by user
    _args = parser.parse_args()
    if _args.threads < 1:
        raise ValueError('Thread count must be a positive number')

    Logger.SILENT_MODE = _args.quiet
    Logger.DEBUG_MODE = _args.debug
    PRESERVE_PATHS = _args.preserve_paths
    DESTINATION_PATH = _args.destination if _args.destination else os.getcwd()
    Downloader.thread_limit = int(_args.threads)

    return _args


def exit_with_error(msg):
    log.error(msg)
    sys.exit(1)


class Downloader:
    __started = False
    __abort = False
    links = []
    temp_files = []
    thread_limit = 1
    completed_urls = []

    def __init__(self, url_list_file, download_delay=0):
        self.url_list_file = url_list_file
        self.download_delay = download_delay
        self.__fetch_url_list()

    def __fetch_url_list(self):
        with open(self.url_list_file, 'r') as f:
            body = f.read()
        final_list = []

        # Dedupe but preserve original order
        for url in [u for u in re.split(r'[\r\n]+', body) if u]:
            if url not in final_list:
                final_list.append(url)

        self.links = final_list

    def remove_temp_file(self, file):
        """ Remove a temp file from the internal tracking list """
        while file in self.temp_files:
            del self.temp_files[self.temp_files.index(file)]

    def __update_download_bar(self, msg):
        if not log.SILENT_MODE and self.thread_limit == 1:
            if not msg:
                print()
            else:
                sys.stdout.write(msg)
                sys.stdout.flush()

    def update_url_file(self):
        with open(self.url_list_file, 'w+') as f:
            f.write('\n'.join(self.links))

    def __complete_url(self, url):
        """ To mark a URL as completed, add to completed_urls list and delete from links list """
        self.completed_urls.append(url)
        del self.links[self.links.index(url)]

    def abort(self):
        self.__abort = True

    def download_with_progress_bar(self, url, file_name=None):
        if self.__abort:
            return
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
        if os.path.exists(final_file_path):
            log.info(f'Already exists; skipped: {url}')
            self.__complete_url(url)
            return False

        # pause momentarily between downloads to go easy on the remote site
        if not self.__started:
            self.__started = True
        elif self.download_delay:
            log.debug(f'Sleeping for {int(self.download_delay) if int(self.download_delay) == self.download_delay else self.download_delay} seconds before next download')
            time.sleep(self.download_delay)

        log.info(f'\nDownloading: {file_name} [{url}]')
        self.temp_files.append(temp_file)
        response = requests.get(url, stream=True)
        with open(temp_file, 'wb') as f:
            total_length = response.headers.get('content-length')
            if total_length is None:  # no content length header
                f.write(response.content)
            else:
                total_length = int(total_length)
                if log.SILENT_MODE or self.thread_limit > 1:
                    for data in response.iter_content(chunk_size=4096):
                        if self.__abort:
                            log.debug("Aborting...")
                            return
                        f.write(data)
                else:
                    for chunk in progress.bar(response.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
                        if self.__abort:
                            log.debug("Aborting...")
                            return
                        if chunk:
                            f.write(chunk)
                            f.flush()
                    print()

        if not os.path.exists(download_path):
            log.debug(f'Creating subfolder(s): "{download_path}"')
            Path(download_path).mkdir(parents=True, exist_ok=True)
        log.debug(f'Renaming temp file: "{temp_file}" ==> "{final_file_path}"')
        os.rename(temp_file, final_file_path)
        self.remove_temp_file(temp_file)
        self.__complete_url(url)


log = Logger()


def main():
    args = get_args()
    sleep_time = args.sleep or 0
    log.debug(f'Starting at {time.strftime("%Y-%m-%d %H-%M-%S")}')
    log.debug(f'Processing URL file [{args.url_file}]')
    downloader = Downloader(args.url_file, download_delay=sleep_time)

    with concurrent.futures.ThreadPoolExecutor(max_workers=downloader.thread_limit) as executor:
        try:
            futures = [executor.submit(downloader.download_with_progress_bar, url) for url in downloader.links]
            for future in concurrent.futures.as_completed(futures):
                _ = future.result()
                downloader.update_url_file()
                log.debug('Download task completed')
        except KeyboardInterrupt:
            downloader.abort()
            executor.shutdown(wait=False)
            if downloader:
                for file in downloader.temp_files:
                    log.warn(f'\n\nTemp file remains and must be manually deleted: {file}')
            exit_with_error("\n\nControl-C Pressed; stopping...")
        else:
            log.info('\nDone!')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit_with_error("\n\nControl-C Pressed; stopping...")
