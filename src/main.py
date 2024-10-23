import asyncio
import sys
import logging
from usecases.essays import GetMaxWordCountsFromEssays

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    first_parameter = input("Please provide File Path: ")
    top_words = input("Please provide number of top words to return(Default 10): ")
    try:
        with open(first_parameter, mode="r", newline='') as file:
            https_urls = file.readlines()
    except FileNotFoundError:
        logging.error("We were not able to locate the file, Please provide correct path.")
        sys.exit(1)
    except Exception as ex:
        logging.error(f"We found some issue reading the file, Please check file and try again.: {ex}")
        sys.exit(1)

    file_name = first_parameter.split("/")[-1]
    client_input = {
        "http_urls": https_urls,
        "file_name": file_name
    }
    if top_words:
        client_input['top_words'] = int(top_words)
    upload_use_case = GetMaxWordCountsFromEssays(**client_input)
    asyncio.run(upload_use_case.execute())
