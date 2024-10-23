import unittest
from unittest.mock import patch, MagicMock, mock_open
import asyncio
from collections import Counter
from fastapi.responses import JSONResponse
from src.usecases.essays import GetMaxWordCountsFromEssays


class TestGetMaxWordCountsFromEssays(unittest.TestCase):

    def setUp(self):
        self.urls = ['http://example.com', 'http://example.org']
        self.use_case = GetMaxWordCountsFromEssays(self.urls)

    @patch('src.usecases.essays.requests.get')
    def test_get_word_banks(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "apple\nbanana\ncherry\n"
        mock_get.return_value = mock_response

        word_banks = asyncio.run(self.use_case.get_word_banks())

        self.assertEqual(word_banks, {'apple', 'banana', 'cherry'})
        mock_get.assert_called_once_with(self.use_case.word_banks_url)

    @patch('src.usecases.essays.aiohttp.ClientSession')
    @patch('src.usecases.essays.BeautifulSoup')
    async def test_fetch_and_filter_content(self, mock_bs, mock_session):
        url = 'http://example.com'
        word_bank = {'apple', 'banana', 'cherry'}
        mock_response = MagicMock()
        mock_response.text.return_value = asyncio.Future()
        mock_response.text.return_value.set_result('apple banana cherry date')
        mock_session.get.return_value.__aenter__.return_value = mock_response

        mock_soup = MagicMock()
        mock_soup.get_text.return_value = 'apple banana cherry date'
        mock_bs.return_value = mock_soup

        semaphore = asyncio.Semaphore(1)
        failed_urls = []
        processed_urls = {}

        result = await self.use_case.fetch_and_filter_content(
            url, word_bank, mock_session, semaphore, failed_urls, processed_urls)

        self.assertEqual(result, ['apple', 'banana', 'cherry'])
        self.assertEqual(processed_urls, {url: Counter(['apple', 'banana', 'cherry'])})
        self.assertEqual(failed_urls, [])

    @patch('src.usecases.essays.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_write_to_json(self, mock_file, mock_json_dump):
        processed_urls = {'http://example.com': Counter({'apple': 2, 'banana': 1})}
        self.use_case.write_to_json(processed_urls)
        mock_file.assert_called_once_with(self.use_case.cached_file, 'w')
        mock_json_dump.assert_called_once()

    def test_aggregate_word_counts(self):
        data = {
            'url1': {'apple': 2, 'banana': 1},
            'url2': {'apple': 1, 'cherry': 2}
        }
        result = self.use_case.aggregate_word_counts(data)
        self.assertEqual(result, {'apple': 3, 'banana': 1, 'cherry': 2})

    def test_get_top_words(self):
        data = {
            'url1': {'apple': 2, 'banana': 1},
            'url2': {'apple': 1, 'cherry': 2}
        }
        result = self.use_case.get_top_words(data)
        self.assertEqual(result, {'apple': 3, 'cherry': 2, 'banana': 1})

    @patch('src.usecases.essays.GetMaxWordCountsFromEssays.get_word_banks')
    @patch('src.usecases.essays.GetMaxWordCountsFromEssays.fetch_and_filter_batch')
    @patch('src.usecases.essays.GetMaxWordCountsFromEssays.write_to_json')
    @patch('src.usecases.essays.GetMaxWordCountsFromEssays.get_top_words')
    async def test_execute(self, mock_get_top_words, mock_write_to_json, mock_fetch_and_filter_batch,
                           mock_get_word_banks):
        mock_get_word_banks.return_value = {'apple', 'banana', 'cherry'}
        mock_fetch_and_filter_batch.return_value = (['apple', 'banana', 'cherry'], [])
        mock_get_top_words.return_value = {'apple': 3, 'banana': 2, 'cherry': 1}

        response = await self.use_case.execute()
        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, {'top_words': {'apple': 3, 'banana': 2, 'cherry': 1}, 'failed_urls': []})


if __name__ == '__main__':
    unittest.main()