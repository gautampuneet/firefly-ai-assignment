import json
import os
import aiohttp
import asyncio
import logging
import requests
import random
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set
from common.constants import Configuration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class GetMaxWordCountsFromEssays:

    def __init__(self, http_urls: List[str],
                 top_words: int = Configuration.DEFAULT_TOP_WORDS_COUNT):
        """Initialize the use case with parameters for processing URLs.

        Args:
            http_urls (list): List of URLs to process.
            top_words(int): Numbers of top words to fetch
        """
        self.http_urls = set(http_urls)
        self.word_banks_url = Configuration.WORDS_BANK_URL
        self.batch_size = Configuration.DEFAULT_PROCESSING_BATCH_SIZE
        self.max_concurrent_requests = Configuration.DEFAULT_MAX_CONCURRENT_REQUESTS  # Control concurrency
        self.top_words = top_words
        self.cached_file = Configuration.PROCESSED_LINKS_JSON_FILE_PATH
        self.already_processed_urls = self.read_json_file()

    async def execute(self):
        """Execute the main process of fetching and filtering words from the provided URLs.

        This method processes the URLs in batches, filters the words against the word bank,
        writes the filtered results to a CSV file, and retrieves the top 10 words from the results.

        Returns:
            JSONResponse: Contains the top words and any failed URLs.
        """
        failed_urls = []
        # Fetch the list of valid words
        word_banks = await self.get_word_banks()

        # Get Already processed Urls
        filtered_urls = [url for url in self.http_urls if url not in self.already_processed_urls]
        # Process URLs in batches
        for batch_start in range(0, len(filtered_urls), self.batch_size):
            processed_urls = {}
            batch_urls = filtered_urls[batch_start: batch_start + self.batch_size]
            logging.info(f"Processing batch {batch_start // self.batch_size + 1}...")
            filtered_words, failed_urls = await self.fetch_and_filter_batch(batch_urls, word_banks, processed_urls)
            self.write_to_json(processed_urls)

        # Read the filtered words from the output file and get the top 10
        with open(self.cached_file, 'r') as file:
            data = file.read()
            if not data:
                top_words = []
            else:
                data = json.loads(data)
                top_words = self.get_top_words(data)

        # Prepare the response with top words and any failed URLs
        response = {
            "top_words": top_words,
            "failed_urls": failed_urls
        }
        logging.info(f"Response: {json.dumps(response, indent=4)}")

    async def get_word_banks(self) -> set:
        """Fetch word banks asynchronously and store them in a set for quick lookup.

        Returns:
            set: A set of valid words (minimum length of 3 and alphabetical).
        """
        response = requests.get(self.word_banks_url)
        if response.status_code == 200:
            word_list = response.text.splitlines()
            # Filter valid words
            return {word.strip() for word in word_list if word.isalpha() and len(word) > 2}

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
            while retries < Configuration.MAX_RETRY_FOR_BACKOFF:
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
                        words = [word.strip() for word in words if word in word_bank]
                        processed_urls[url] = Counter(words)
                        return words

                except asyncio.TimeoutError as e:
                    retries += 1
                    wait_time = random.uniform(2, 2 ** retries)
                    logging.warning(f"Rate Limit Error fetching {url}: {e}. Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                except aiohttp.ClientError as e:
                    logging.warning(f"Client Error fetching {url}: {e}")
                    failed_urls.append(url)
                    return []
            logging.error(f"Failed to fetch {url} after {retries} retries.")

    def write_to_json(self, processed_urls: Dict) -> None:
        """Write filtered words to a CSV file.

        Args:
            processed_urls(Dict): Processed Urls with their Values
        """
        data = {}
        if os.path.exists(self.cached_file):
            with open(self.cached_file, 'r') as file:
                data = json.load(file)

        data.update(processed_urls)
        with open(self.cached_file, 'w') as file:
            json.dump(data, file, indent=4)

    def read_json_file(self):
        if os.path.exists(self.cached_file):
            with open(self.cached_file, 'r') as file:
                data = json.load(file)
                return data
        return {}

    @staticmethod
    def aggregate_word_counts(data: Dict) -> Dict:
        # Create a default dictionary to hold total word counts
        total_counts = defaultdict(int)

        # Iterate through each URL's word dictionary
        for url, word_counts in data.items():
            for word, count in word_counts.items():
                total_counts[word] += count  # Aggregate counts
        return total_counts

    def get_top_words(self, words_list: Dict) -> Dict:
        """Get the top 10 most frequent words from the filtered content.

        Args:
            words_list (dict): Dict of words to analyze.

        Returns:
            dict: A dictionary of the top 10 words and their counts.
        """
        # Count occurrences of each word
        total_counts = self.aggregate_word_counts(words_list)
        sorted_words = sorted(total_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_words[:self.top_words])
