class EssaysRoutes:
    PREFIX = "/v1"
    BASE_PATH = "/essays"
    BULK_FILE = f"{BASE_PATH}/bulk"
    GET_ESSAYS_BY_ID = f"{BASE_PATH}/{{file_id}}"
    TAGS = ["Essays"]
