from src.essays.common.constants import EssayConfiguration


class EssayErrorMessages:
    FILE_LIMIT_EXCEED = (f"File Limit Exceeded, As of now only"
                         f" {EssayConfiguration.MAX_HTTP_URLS_SUPPORTED_FOR_API} urls are supported.")
    FILE_DOES_NOT_EXIST = "File id does not exist, Please verify and try again."
    FILE_STILL_GETTING_PROCESSED = "File is Still Getting Processed, Please check after sometime."
