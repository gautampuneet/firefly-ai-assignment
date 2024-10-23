import unittest
from unittest.mock import patch, Mock, AsyncMock
import asyncio
from collections import Counter

from src.essays.usecases.essays import (
    UploadEssaysFileUseCase,
    GetMaxWordCountsFromEssays,
    GetMaxCountsBasedOnID,
    FileStatus
)


class TestUploadEssaysFileUseCase(unittest.TestCase):
    def setUp(self):
        self.test_urls = ["https://test1.com", "https://test2.com"]
        self.file_name = "test_file.txt"
        self.use_case = UploadEssaysFileUseCase(self.test_urls, self.file_name)

    @patch('requests.get')
    async def test_get_word_banks(self, mock_get):
        # Mock response for word banks
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "hello\nworld\ntest\n"
        mock_get.return_value = mock_response

        # Run the test
        word_banks = await self.use_case.get_word_banks()

        self.assertIsInstance(word_banks, set)
        self.assertTrue(all(len(word) > 2 for word in word_banks))
        self.assertTrue(all(word.isalpha() for word in word_banks))

    @patch('requests.get')
    async def test_get_word_banks_failed(self, mock_get):
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Run the test
        word_banks = asyncio.run(self.use_case.get_word_banks())

        self.assertEqual(word_banks, set())

    @patch('aiohttp.ClientSession')
    async def test_fetch_and_filter_content(self, mock_session):
        # Mock setup
        url = "https://test.com"
        word_bank = {"test", "content"}
        mock_response = AsyncMock()
        mock_response.text.return_value = "<html>test content test</html>"
        mock_response.status = 200

        mock_session_context = AsyncMock()
        mock_session_context.__aenter__.return_value = mock_response
        mock_session.get.return_value = mock_session_context

        semaphore = asyncio.Semaphore(1)
        failed_urls = []
        processed_urls = {}

        # Run the test
        result = await self.use_case.fetch_and_filter_content(
            url, word_bank, mock_session, semaphore, failed_urls, processed_urls
        )

        self.assertIsInstance(result, list)
        self.assertTrue(all(word in word_bank for word in result))

    @patch('aiohttp.ClientSession')
    async def test_fetch_and_filter_batch(self):
        # Mock setup
        batch_urls = ["https://test1.com", "https://test2.com"]
        word_banks = {"test", "content"}
        processed_urls = {}

        # Run the test
        filtered_words, failed_urls = await self.use_case.fetch_and_filter_batch(
            batch_urls, word_banks, processed_urls
        )

        self.assertIsInstance(filtered_words, list)
        self.assertIsInstance(failed_urls, list)

    @patch('src.common.utility.write_to_json')
    @patch('src.common.utility.read_json_file')
    async def test_execute(self, mock_read_json, mock_write_json):
        # Mock setup
        mock_read_json.return_value = {}
        mock_write_json.return_value = None

        # Run the test
        result = await self.use_case.execute()

        self.assertIsInstance(result, dict)
        self.assertIn("failed_urls", result)
        self.assertIn("file_id", result)


class TestGetMaxWordCountsFromEssays(unittest.TestCase):
    def setUp(self):
        self.test_urls = ["https://test1.com", "https://test2.com"]
        self.file_name = "test_file.txt"
        self.use_case = GetMaxWordCountsFromEssays(self.test_urls, self.file_name)

    @patch('src.usecases.essays.UploadEssaysFileUseCase')
    async def test_execute(self, mock_upload_use_case):
        # Mock setup
        mock_upload_use_case.return_value.execute.return_value = {
            "failed_urls": [],
            "file_id": "test_file_id"
        }

        # Run the test
        result = await self.use_case.execute()

        self.assertIsInstance(result, dict)
        self.assertIn("top_words", result)
        self.assertIn("failed_urls", result)
        self.assertIn("file_id", result)


class TestGetMaxCountsBasedOnID(unittest.TestCase):
    def setUp(self):
        self.file_id = "test_file_id"
        self.use_case = GetMaxCountsBasedOnID(self.file_id)

    @patch('src.common.utility.read_json_file')
    def test_check_status_in_file_not_processed(self, mock_read_json):
        # Mock setup
        mock_read_json.return_value = {
            self.file_id: {
                "status": FileStatus.PROCESSING
            }
        }

        # Run the test
        result = self.use_case.check_status_in_file()

        self.assertEqual(result, (True, {'message': 'File id does not exist, Please verify and try again.'}))

    @patch('src.common.utility.read_json_file')
    def test_get_top_words(self, mock_read_json):
        # Mock setup
        mock_read_json.return_value = {
            "https://test.com": Counter({"test": 2, "content": 1})
        }

        # Run the test
        result = self.use_case.get_top_words(mock_read_json.return_value, ["https://test.com"])

        self.assertIsInstance(result, dict)
        self.assertIn("test", result)
        self.assertIn("content", result)


if __name__ == '__main__':
    unittest.main()
