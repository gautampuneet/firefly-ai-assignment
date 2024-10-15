import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.usecases.essays import UploadEssaysUseCase
import csv
import os


@pytest.fixture
def word_banks_url():
    return "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt"


@pytest.fixture
def word_banks():
    return {"apple", "banana", "cherry"}


@pytest.fixture
def http_urls():
    return [
        "https://www.engadget.com/2019/08/24/bioprint-living-tissue-in-seconds/",
        "https://www.engadget.com/2019/08/24/oneplus-7t-wide-angle-camera-leak/"
    ]


@pytest.fixture
def output_file():
    return "filtered_words.csv"


@pytest.fixture
def upload_use_case(http_urls, output_file):
    return UploadEssaysUseCase(http_urls=http_urls, output_file=output_file)


def test_upload_essays_use_case_init(http_urls, output_file):
    use_case = UploadEssaysUseCase(http_urls=http_urls, output_file=output_file)
    assert use_case.http_urls == http_urls
    assert use_case.output_file == output_file


@pytest.mark.asyncio
async def test_get_word_banks(word_banks_url, word_banks):
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '\n'.join(word_banks)
        mock_get.return_value = mock_response
        use_case = UploadEssaysUseCase()
        result = await use_case.get_word_banks()
        assert result == word_banks


@pytest.mark.asyncio
async def test_get_word_banks_failure(word_banks_url):
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        use_case = UploadEssaysUseCase()
        result = await use_case.get_word_banks()
        assert result == set()


@pytest.mark.asyncio
async def test_fetch_and_filter_batch(upload_use_case, word_banks):
    with patch('src.usecases.essays.UploadEssaysUseCase.fetch_and_filter_content') as mock_fetch_and_filter_content:
        mock_fetch_and_filter_content.return_value = ["apple", "banana", "cherry"]
        result, failed_urls = await upload_use_case.fetch_and_filter_batch(upload_use_case.http_urls, word_banks)
        assert result == ["apple", "banana", "cherry"] * len(upload_use_case.http_urls)
        assert failed_urls == []


@pytest.mark.asyncio
async def test_fetch_and_filter_batch_failure(upload_use_case, word_banks):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value.status = 404
        result, failed_urls = await upload_use_case.fetch_and_filter_batch(upload_use_case.http_urls, word_banks)
        assert result == []
        assert failed_urls == upload_use_case.http_urls


@pytest.mark.asyncio
async def test_fetch_and_filter_content_failure(upload_use_case, word_banks):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value.status = 404
        result = await upload_use_case.fetch_and_filter_content(upload_use_case.http_urls[0], word_banks,
                                                                mock_session.return_value, asyncio.Semaphore(10), [])
        assert result == []


def test_write_to_csv(upload_use_case):
    words = ["apple", "banana", "cherry"]
    upload_use_case.write_to_csv(words)
    with open(upload_use_case.output_file, 'r') as file:
        reader = csv.reader(file)
        result = list(reader)
    assert result == [["apple"], ["banana"], ["cherry"]]
    os.remove(upload_use_case.output_file)


def test_get_top_10_words():
    words = ["apple", "banana", "cherry", "apple", "banana", "banana"]
    result = UploadEssaysUseCase.get_top_10_words(words)
    assert result == {"banana": 3, "apple": 2, "cherry": 1}


def test_execute(upload_use_case, word_banks):
    with patch('src.usecases.essays.UploadEssaysUseCase.get_word_banks') as mock_get_word_banks:
        mock_get_word_banks.return_value = word_banks
        with patch('src.usecases.essays.UploadEssaysUseCase.fetch_and_filter_batch') as mock_fetch_and_filter_batch:
            mock_fetch_and_filter_batch.return_value = (["apple", "banana", "cherry"], [])
            response = asyncio.run(upload_use_case.execute())
            assert response.status_code == 200
            import json
            assert json.loads(response.body) == {"top_words": {"banana": 1, "apple": 1, "cherry": 1}, "failed_urls": []}
