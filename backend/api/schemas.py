from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class _BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------


class UserCreate(_BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserLogin(_BaseSchema):
    email: EmailStr
    password: str


class UserRead(_BaseSchema):
    id: int
    email: EmailStr
    created_at: datetime


class TokenResponse(_BaseSchema):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ---------- Read models ----------


class TripRead(_BaseSchema):
    id: int
    name: str
    currency: str
    created_at: datetime
    share_token: Optional[str] = None


class MemberRead(_BaseSchema):
    id: int
    name: str
    is_self: int


class TripDetailRead(TripRead):
    members: List[MemberRead]


class ExpenseParticipantRead(_BaseSchema):
    id: int
    name: str


class ExpenseRead(_BaseSchema):
    id: int
    description: str
    amount_cents: int
    expense_date: str
    paid_by_member_id: int
    payer_name: str
    notes: Optional[str] = None
    participants: List[ExpenseParticipantRead] = Field(default_factory=list)


class BalanceRead(_BaseSchema):
    member_id: int
    name: str
    is_self: int
    total_paid: int
    total_share: int
    net_balance: int


class SettlementRead(_BaseSchema):
    from_member_id: int
    from_member_name: str
    to_member_id: int
    to_member_name: str
    amount_cents: int


class SummaryMemberMetric(_BaseSchema):
    name: str
    amount_cents: int


class TripSummaryRead(_BaseSchema):
    trip_name: str
    currency: str
    total_trip_spending: int
    total_expenses: int
    total_members: int
    highest_spender: Optional[SummaryMemberMetric] = None
    member_who_owes_most: Optional[SummaryMemberMetric] = None
    highest_total_share: Optional[SummaryMemberMetric] = None


class HealthResponse(_BaseSchema):
    ok: bool
    service: str = "bill-buddy-api"


# ---------- Create / update models ----------


class MemberCreate(_BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    is_self: bool = False


class TripCreate(_BaseSchema):
    name: str = Field(min_length=1, max_length=200)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    members: List[MemberCreate] = Field(min_length=1)

    @field_validator("currency")
    @classmethod
    def _uppercase_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("members")
    @classmethod
    def _exactly_one_self(cls, value: List[MemberCreate]) -> List[MemberCreate]:
        self_count = sum(1 for member in value if member.is_self)
        if self_count != 1:
            raise ValueError("Exactly one member must have is_self=true")
        return value


class MemberAdd(_BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    is_self: bool = False


class ExpenseCreate(_BaseSchema):
    description: str = Field(min_length=1, max_length=500)
    amount_cents: int = Field(gt=0)
    expense_date: date
    paid_by_member_id: int
    participant_ids: List[int] = Field(min_length=1)
    notes: Optional[str] = None


class ExpenseUpdate(_BaseSchema):
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    amount_cents: Optional[int] = Field(default=None, gt=0)
    expense_date: Optional[date] = None
    paid_by_member_id: Optional[int] = None
    participant_ids: Optional[List[int]] = Field(default=None, min_length=1)
    notes: Optional[str] = None
