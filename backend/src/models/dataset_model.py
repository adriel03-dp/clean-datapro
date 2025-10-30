from pydantic import BaseModel
from typing import Any, Dict


class ProcessResponse(BaseModel):
    raw_file: str
    cleaned_file: str
    report_file: str
    json_summary: str
    summary: Dict[str, Any]
