from pydantic import BaseModel
from typing import Optional


class DriverConfig(BaseModel):
    license_number: str
    last_name: str
    exam_type: str
    login_keyword: str
    icbc_office_id: Optional[int]
