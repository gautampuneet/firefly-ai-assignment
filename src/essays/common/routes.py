class EssaysRoutes:
    PREFIX = "/v1"
    BASE_PATH = "/essays"
    BULK_FILE = f"{BASE_PATH}/bulk"
    GET_ESSAYS_BY_ID = f"{BASE_PATH}/{{file_id}}"
    TAGS = ["Essays"]


class RoutesDescription:
    class BulkFile:
        DESCRIPTION = """
            Upload a large file containing URLs. The processing will be handled asynchronously in the background.
            
            ### Process Overview:
            - Upload a file (containing a large number of URLs).
            - Will return `File ID` in response.
            - The system will start processing the URLs in the background.
            - Once the processing is completed.
            - You can use the `File ID` to fetch the output through a `/v1/essays/{file_id} API`.
            
            This allows you to submit large files without waiting for the entire processing to complete.
        """
        SUMMARY = "Upload Large Files Containing urls"

    class SmallFileProcess:
        SUMMARY = "Upload File with Maximum limit of 20 Urls"
        DESCRIPTION = """
            Upload File containing URLs. Processing will be done instantly.
            
            ### Process Overview:
            - Upload a file (Containing Maximum 20 Urls)
            - Server will process the Urls
            - Return Maximum Occurrence words count 
        """

    class GetMaxOccurrenceByID:
        SUMMARY = "Get the Maximum Occurrence Count based on File ID"
