from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class WorkLogListItem(BaseModel):
    id: UUID
    user_id: UUID
    remittance_id: UUID | None
    amount: float
    created_at: datetime

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value is None:
            raise ValueError("amount is required")
        if not isinstance(value, (int, float)):
            raise ValueError("amount must be a number")
        return float(value)


class WorkLogListResponse(BaseModel):
    data: list[WorkLogListItem]
    count: int

    @field_validator("count")
    @classmethod
    def validate_count(cls, value: int) -> int:
        if value is None:
            raise ValueError("count is required")
        if not isinstance(value, int):
            raise ValueError("count must be an integer")
        if value < 0:
            raise ValueError("count cannot be negative")
        return value


class RemittanceGenerated(BaseModel):
    id: UUID
    user_id: UUID
    amount: float
    status: str
    created_at: datetime


class GenerateRemittancesResponse(BaseModel):
    remittances: list[RemittanceGenerated]
