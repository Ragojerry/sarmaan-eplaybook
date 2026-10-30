import uuid
from datetime import date

from fastapi import Query

from app.models.enums import RoleName
from app.reports.activity import Filters


def report_filters(
    country_id: uuid.UUID | None = Query(default=None),
    state_id: uuid.UUID | None = Query(default=None),
    lga_id: uuid.UUID | None = Query(default=None),
    ward_id: uuid.UUID | None = Query(default=None),
    facility_id: uuid.UUID | None = Query(default=None),
    session_id: uuid.UUID | None = Query(default=None, description="Limit to one training session."),
    role: RoleName | None = Query(default=RoleName.CDD, description="Defaults to CDD (the people being trained)."),
    all_roles: bool = Query(default=False, description="Include every role."),
    team_code: str | None = Query(default=None, max_length=20),
    date_from: date | None = Query(default=None, description="Limit activity to this period (YYYY-MM-DD)."),
    date_to: date | None = Query(default=None),
) -> Filters:
    return Filters(
        country_id=country_id, state_id=state_id, lga_id=lga_id, ward_id=ward_id, facility_id=facility_id, session_id=session_id,
        role=None if all_roles else role, team_code=team_code, date_from=date_from, date_to=date_to,
    )
