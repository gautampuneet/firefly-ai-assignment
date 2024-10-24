import json
import uuid

import aiohttp
import asyncio
import logging
import requests
import random
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set
from src.essays.common.constants import EssayConfiguration, FileStatus
from src.essays.common.error_messages import EssayErrorMessages
from src.common.utility import read_json_file, create_tmp_folder, write_to_json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class UploadEssaysFileUseCase:

    def __init__(self, http_urls, file_name, file_id=None):
        self.http_urls = set(http_urls)
        self.file_name = file_name
        self.file_id = file_id
        self.word_banks_url = EssayConfiguration.WORDS_BANK_URL
        self.batch_size = EssayConfiguration.DEFAULT_PROCESSING_BATCH_SIZE
        self.max_concurrent_requests = EssayConfiguration.DEFAULT_MAX_CONCURRENT_REQUESTS  # Control concurrency
        self.cached_file = EssayConfiguration.PROCESSED_LINKS_JSON_FILE_PATH
        self.already_processed_urls = read_json_file(file_directory=self.cached_file)

    async def execute(self):
        failed_urls = []
        file_status = FileStatus.PROCESSING
        try:
            # Create Temp File to store data
            create_tmp_folder(EssayConfiguration.PROCESSED_CACHED_FOLDER)

            logging.info(f"File processing has started.")
            # Update the Status as processing first
            file_id = str(uuid.uuid4()) if not self.file_id else self.file_id
            processed_file_data = {
                file_id: {
                    "file_name": self.file_name,
                    "status": FileStatus.PROCESSING,
                    "http_urls": list(self.http_urls),
                    "failed_urls": failed_urls
                }
            }
            write_to_json(
                file_path=EssayConfiguration.PROCESSED_FILES_JSON_FILE_PATH,
                data=processed_file_data
            )

            # Fetch the list of valid words
            word_banks = await self.get_word_banks()

            # Get Already processed Urls
            filtered_urls = [url for url in self.http_urls if url and url not in self.already_processed_urls]
            # Process URLs in batches
            for batch_start in range(0, len(filtered_urls), self.batch_size):
                processed_urls = {}
                batch_urls = filtered_urls[batch_start: batch_start + self.batch_size]
                logging.info(f"Processing batch {batch_start // self.batch_size + 1}...")
                filtered_words, failed_urls = await self.fetch_and_filter_batch(batch_urls, word_banks, processed_urls)
                write_to_json(data=processed_urls, file_path=self.cached_file)

            file_status = FileStatus.PROCESSED
        except Exception as ex:
            logging.error(f"Error Processing the File, {ex}")
            file_status = FileStatus.FAILED
        finally:
            # Update the File status in the DB
            file_id = str(uuid.uuid4()) if not self.file_id else self.file_id
            processed_file_data = {
                file_id: {
                    "file_name": self.file_name,
                    "status": file_status,
                    "http_urls": list(self.http_urls),
                    "failed_urls": failed_urls
                }
            }
            write_to_json(
                file_path=EssayConfiguration.PROCESSED_FILES_JSON_FILE_PATH,
                data=processed_file_data
            )
        return {"failed_urls": failed_urls, "file_id": file_id}

    async def get_word_banks(self) -> set:
        """Fetch word banks asynchronously and store them in a set for quick lookup.

        Returns:
            set: A set of valid words (minimum length of 3 and alphabetical).
        """
        response = requests.get(self.word_banks_url)
        if response.status_code == 200:
            word_list = response.text.splitlines()
            # Filter valid words
            return {word.strip().lower() for word in word_list if word.isalpha() and len(word) > 2}

        # Return an empty set if fetching fails
        return set()

    async def fetch_and_filter_batch(self,
                                     batch_urls: List[str],
                                     word_banks: Set[str],
                                     processed_urls: Dict) -> Tuple[List[str], List]:
        """Fetch and filter a batch of URLs concurrently.

        Args:
            batch_urls (List): List of URLs to fetch and filter.
            word_banks (set): Set of valid words to filter against.
            processed_urls(Dict): To Keep Track which url has been processed
        Returns:
            tuple: A list of filtered words and a list of failed URLs.
        """
        failed_urls = []
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)  # Limit concurrent requests
        async with aiohttp.ClientSession() as session:
            # Create tasks for fetching and filtering each URL
            tasks = [self.fetch_and_filter_content(url,
                                                   word_banks,
                                                   session,
                                                   semaphore,
                                                   failed_urls,
                                                   processed_urls)
                     for url in batch_urls]
            # Await all tasks to complete
            results = await asyncio.gather(*tasks)
            # Flatten the filtered results into a single list
            return [word.strip() for result in results for word in result if result], failed_urls

    @staticmethod
    async def fetch_and_filter_content(url: str,
                                       word_bank: Set[str],
                                       session: aiohttp.ClientSession,
                                       semaphore: asyncio.Semaphore,
                                       failed_urls: List[str],
                                       processed_urls: Dict) -> List[str]:
        """Fetch content of a single URL asynchronously and filter it against the word bank.

        Args:
            url (str): The URL to fetch.
            word_bank (set): Set of valid words to filter against.
            session (ClientSession): A session object for making HTTP requests.
            semaphore (Semaphore): A semaphore to limit the number of concurrent requests.
            failed_urls (list): List to track URLs that failed to fetch.
            processed_urls(Dict): To Keep Track which url has been processed

        Returns:
            list: A list of filtered words from the URL content.
        """
        async with semaphore:
            retries = 0
            while retries < EssayConfiguration.MAX_RETRY_FOR_BACKOFF:
                try:
                    async with session.get(url) as response:
                        if response.status == 429:  # Too many requests
                            raise asyncio.TimeoutError("Rate limited")

                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        # Extract visible text
                        text = soup.get_text()
                        # Split text into words
                        words = text.split()
                        # Filter words on-the-fly
                        words = [word.strip().lower() for word in words if word in word_bank]
                        processed_urls[url] = Counter(words)
                        return words

                except asyncio.TimeoutError as e:
                    retries += 1
                    wait_time = random.uniform(2, 2 ** retries)
                    logging.warning(f"Rate Limit Error fetching {url}: {e}. Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                except aiohttp.ClientError as e:
                    logging.warning(f"Client Error fetching {url}: {e}")
                    break

            logging.error(f"Failed to fetch {url} after {retries} retries.")
            failed_urls.append(url)
            return []


class GetMaxWordCountsFromEssays:

    def __init__(self,
                 http_urls: List[str],
                 file_name: str,
                 top_words: int = EssayConfiguration.DEFAULT_TOP_WORDS_COUNT,
                 file_id: str = None
                 ):
        """Initialize the use case with parameters for processing URLs.

        Args:
            http_urls (list): List of URLs to process.
            top_words(int): Numbers of top words to fetch
            file_name(str): Name of the file getting processed
            file_id(str): File Id that we are processing
        """
        self.http_urls = http_urls
        self.top_words = top_words
        self.file_name = file_name
        self.file_id = file_id
        self.cached_file = EssayConfiguration.PROCESSED_LINKS_JSON_FILE_PATH

    async def execute(self):
        """Execute the main process of fetching and filtering words from the provided URLs.

        This method processes the URLs in batches, filters the words against the word bank,
        writes the filtered results to a CSV file, and retrieves the top 10 words from the results.

        Returns:
            JSONResponse: Contains the top words and any failed URLs.
        """

        # Process the Urls and Save Every Word Count
        response = await UploadEssaysFileUseCase(
            http_urls=self.http_urls,
            file_name=self.file_name
        ).execute()

        # Read the filtered words from the output file and get the top 10
        final_response = GetMaxCountsBasedOnID(
            file_id=response.get("file_id"),
            top_words=self.top_words
        ).execute()
        logging.info(f"Response: {json.dumps(final_response, indent=4)}")
        return final_response


class GetMaxCountsBasedOnID:

    def __init__(self,
                 file_id: str,
                 top_words: int):
        self.file_id = file_id
        self.top_words = top_words

    def execute(self):
        if not self.top_words:
            self.top_words = EssayConfiguration.DEFAULT_TOP_WORDS_COUNT
        # Check File Status
        error, content = self.check_status_in_file()
        if error:
            return content
        http_urls = content["http_urls"]
        failed_urls = content["failed_urls"]

        with open(EssayConfiguration.PROCESSED_LINKS_JSON_FILE_PATH, 'r') as file:
            data = file.read()
            if not data:
                top_words = []
            else:
                data = json.loads(data)
                top_words = self.get_top_words(data, http_urls)

        # Prepare the response with top words and any failed URLs
        response = {
            "top_words": top_words,
            "failed_urls": failed_urls,
            "file_id": self.file_id
        }
        return response

    def check_status_in_file(self) -> Tuple[bool, dict]:
        processed_files = read_json_file(file_directory=EssayConfiguration.PROCESSED_FILES_JSON_FILE_PATH)
        if self.file_id in processed_files and processed_files[self.file_id].get("status") == FileStatus.PROCESSED:
            return False, processed_files[self.file_id]
        elif self.file_id not in processed_files:
            return True, {"message": EssayErrorMessages.FILE_DOES_NOT_EXIST}
        return True, {"message": EssayErrorMessages.FILE_STILL_GETTING_PROCESSED}

    @staticmethod
    def aggregate_word_counts(data: Dict, https_urls: List[str]) -> Dict:
        # Create a default dictionary to hold total word counts
        total_counts = defaultdict(int)

        # Iterate through each URL's word dictionary
        for url, word_counts in data.items():
            if url not in https_urls:
                continue
            for word, count in word_counts.items():
                total_counts[word] += count  # Aggregate counts
        return total_counts

    def get_top_words(self, words_list: Dict, https_urls: List[str]) -> Dict:
        """Get the top 10 most frequent words from the filtered content.

        Args:
            words_list (dict): Dict of words to analyze.
            https_urls(list): List of http urls to filter

        Returns:
            dict: A dictionary of the top 10 words and their counts.
        """
        # Count occurrences of each word
        total_counts = self.aggregate_word_counts(words_list, https_urls)
        sorted_words = sorted(total_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_words[:self.top_words])
