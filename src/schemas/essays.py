from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional


class UploadEssays(BaseModel):
    links: Optional[List[HttpUrl]]

    @validator('links')
    def check_valid_project_url(cls, v):
        string_converted_urls = []
        for link in v:
            link = str(link)
            string_converted_urls.append(link)
        return string_converted_urls
