from src.common.constants import Configuration


class EssayErrorMessages:
    FILE_LIMIT_EXCEED = (f"File Limit Exceeded, As of now only"
                         f" {Configuration.MAX_HTTP_URLS_SUPPORTED_FOR_API} urls are supported.")
