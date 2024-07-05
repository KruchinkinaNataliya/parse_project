from pydantic import BaseModel
from typing import Optional


class VacancyFilter(BaseModel):
    name: str
    salary_from: Optional[int | None]
    salary_to: Optional[int | None]
    employment_status: Optional[str | None]
    work_experience: Optional[str | None]
    employer: Optional[str | None]
    city: Optional[str | None]
