import os
import time

import aiohttp
import asyncio
import logging
import csv
import requests
from bs4 import BeautifulSoup
from collections import Counter
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class UploadEssaysUseCase:

    def __init__(self, http_urls=None, batch_size=1000, max_concurrent_requests=10,
                 output_file='filtered_words.csv'):
        """Initialize the use case with parameters for processing URLs.

        Args:
            http_urls (list): List of URLs to process.
            batch_size (int): Number of URLs to process in each batch to manage memory.
            max_concurrent_requests (int): Maximum number of concurrent requests to control load.
            output_file (str): Path to the CSV file where filtered words will be saved.
        """
        self.http_urls = http_urls or []
        self.word_banks_url = "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt"
        self.batch_size = batch_size  # Process URLs in batches to avoid memory overload
        self.max_concurrent_requests = max_concurrent_requests  # Control concurrency
        self.output_file = output_file  # File to store intermediate filtered results

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

        # Process URLs in batches
        for batch_start in range(0, len(self.http_urls), self.batch_size):
            batch_urls = self.http_urls[batch_start: batch_start + self.batch_size]
            logging.info(f"Processing batch {batch_start // self.batch_size + 1}...")
            filtered_words, failed_urls = await self.fetch_and_filter_batch(batch_urls, word_banks)
            # Save filtered words to CSV
            self.write_to_csv(filtered_words)

        # Read the filtered words from the output file and get the top 10
        with open(self.output_file, 'r', newline='') as file:
            words = file.read().replace('\r', '').splitlines()
            top_words = self.get_top_10_words(words)

        # Prepare the response with top words and any failed URLs
        response = {
            "top_words": top_words,
            "failed_urls": failed_urls
        }
        logging.info(f"Response: {response}")
        os.remove(self.output_file)  # Clean up by removing the output file
        return JSONResponse(
            status_code=200,
            content=response
        )

    async def get_word_banks(self):
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

    async def fetch_and_filter_batch(self, batch_urls, word_banks):
        """Fetch and filter a batch of URLs concurrently.

        Args:
            batch_urls (list): List of URLs to fetch and filter.
            word_banks (set): Set of valid words to filter against.

        Returns:
            tuple: A list of filtered words and a list of failed URLs.
        """
        failed_urls = []
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)  # Limit concurrent requests
        async with aiohttp.ClientSession() as session:
            # Create tasks for fetching and filtering each URL
            tasks = [self.fetch_and_filter_content(url, word_banks, session, semaphore, failed_urls)
                     for url in batch_urls]
            # Await all tasks to complete
            results = await asyncio.gather(*tasks)
            # Flatten the filtered results into a single list
            return [word.strip() for result in results for word in result if result], failed_urls

    @staticmethod
    async def fetch_and_filter_content(url, word_bank, session, semaphore, failed_urls):
        """Fetch content of a single URL asynchronously and filter it against the word bank.

        Args:
            url (str): The URL to fetch.
            word_bank (set): Set of valid words to filter against.
            session (ClientSession): A session object for making HTTP requests.
            semaphore (Semaphore): A semaphore to limit the number of concurrent requests.
            failed_urls (list): List to track URLs that failed to fetch.

        Returns:
            list: A list of filtered words from the URL content.
        """
        async with semaphore:  # Limit concurrency
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        # Extract visible text
                        text = soup.get_text()
                        # Split text into words
                        words = text.split()
                        # Filter words on-the-fly
                        return [word.strip() for word in words if word in word_bank]
            except Exception as e:
                # Log the error and track the failed URL
                logging.info(f"Failed to fetch {url}: {e}")
                failed_urls.append(url)
        # Return an empty list if fetching fails
        return []

    def write_to_csv(self, filtered_words):
        """Write filtered words to a CSV file.

        Args:
            filtered_words (list): List of words to write to the CSV file.
        """
        with open(self.output_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for word in filtered_words:
                # Write each word as a new row
                writer.writerow([word])

    @staticmethod
    def get_top_10_words(word_list):
        """Get the top 10 most frequent words from the filtered content.

        Args:
            word_list (list): List of words to analyze.

        Returns:
            dict: A dictionary of the top 10 words and their counts.
        """
        # Count occurrences of each word
        word_counts = Counter(word_list)

        # Return the 10 most common words
        return dict(word_counts.most_common(10))


if __name__ == "__main__":
    start_time = time.time()
    https_urls = [
        "https://www.engadget.com/2019/08/24/bioprint-living-tissue-in-seconds/",
        "https://www.engadget.com/2019/08/24/oneplus-7t-wide-angle-camera-leak/"
    ]
    upload_use_case = UploadEssaysUseCase(http_urls=https_urls)
    asyncio.run(upload_use_case.execute())
    logging.info(f"Finish time: {time.time() - start_time}")
