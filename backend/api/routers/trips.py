import csv
from io import StringIO
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from api.auth import generate_share_token
from api.database import get_db
from api.dependencies import (
    get_current_user,
    get_owned_expense,
    get_owned_trip,
)
from api.models import Expense, ExpenseParticipant, Member, Trip, User
from api.schemas import (
    BalanceRead,
    ExpenseCreate,
    ExpenseRead,
    MemberAdd,
    MemberRead,
    SettlementRead,
    SummaryMemberMetric,
    TripCreate,
    TripDetailRead,
    TripRead,
    TripSummaryRead,
)
from api.serializers import serialize_expense
from utils.calculations import (
    calculate_net_balance_by_member,
    calculate_total_owed_share_by_member,
    calculate_total_paid_by_member,
    simplify_settlements,
)
from utils.helpers import format_cents

router = APIRouter(prefix="/api/trips", tags=["trips"])


# ---------- Shared helpers (used by trips + share routers) ----------


def load_expenses(
    db: Session,
    trip_id: int,
    payer_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Expense]:
    stmt = (
        select(Expense)
        .where(Expense.trip_id == trip_id)
        .options(
            selectinload(Expense.payer),
            selectinload(Expense.participants).selectinload(ExpenseParticipant.member),
        )
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
    )
    if payer_id is not None:
        stmt = stmt.where(Expense.paid_by_member_id == payer_id)
    if date_from is not None:
        stmt = stmt.where(Expense.expense_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Expense.expense_date <= date_to)
    return list(db.scalars(stmt).all())


def members_to_dicts(trip: Trip) -> list[dict]:
    return [{"id": m.id, "name": m.name, "is_self": m.is_self} for m in trip.members]


def expenses_to_dicts(expenses: List[Expense]) -> list[dict]:
    return [
        {
            "id": e.id,
            "amount_cents": e.amount_cents,
            "paid_by_member_id": e.paid_by_member_id,
        }
        for e in expenses
    ]


def expense_participants_to_dicts(expenses: List[Expense]) -> list[dict]:
    return [
        {"expense_id": e.id, "member_id": ep.member_id}
        for e in expenses
        for ep in e.participants
    ]


def trip_member_ids(trip: Trip) -> set[int]:
    return {member.id for member in trip.members}


def build_csv(trip: Trip, expenses: List[Expense]) -> tuple[str, str]:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Amount", "Paid By", "Participants", "Notes"])
    for expense in expenses:
        writer.writerow(
            [
                expense.expense_date,
                expense.description,
                format_cents(expense.amount_cents, trip.currency),
                expense.payer.name,
                ", ".join(ep.member.name for ep in expense.participants),
                expense.notes or "",
            ]
        )
    filename = f"{_slugify_filename(trip.name)}-expenses.csv"
    return output.getvalue(), filename


def _slugify_filename(value: str) -> str:
    cleaned = value.strip().lower().replace(" ", "-")
    allowed = "".join(c for c in cleaned if c.isalnum() or c in {"-", "_"})
    return allowed.strip("-_") or "bill-buddy-trip"


def build_balances(trip: Trip, expenses: List[Expense]) -> List[BalanceRead]:
    members_dicts = members_to_dicts(trip)
    expenses_dicts = expenses_to_dicts(expenses)
    participants_dicts = expense_participants_to_dicts(expenses)

    paid = calculate_total_paid_by_member(members_dicts, expenses_dicts)
    share = calculate_total_owed_share_by_member(
        members_dicts, expenses_dicts, participants_dicts
    )
    net = calculate_net_balance_by_member(
        members_dicts, expenses_dicts, participants_dicts
    )

    return [
        BalanceRead(
            member_id=m["id"],
            name=m["name"],
            is_self=m["is_self"],
            total_paid=paid[m["id"]],
            total_share=share[m["id"]],
            net_balance=net[m["id"]],
        )
        for m in members_dicts
    ]


def build_settlements(trip: Trip, expenses: List[Expense]) -> List[SettlementRead]:
    members_dicts = members_to_dicts(trip)
    expenses_dicts = expenses_to_dicts(expenses)
    participants_dicts = expense_participants_to_dicts(expenses)
    net = calculate_net_balance_by_member(
        members_dicts, expenses_dicts, participants_dicts
    )
    settlements = simplify_settlements(net)
    member_names = {m["id"]: m["name"] for m in members_dicts}

    return [
        SettlementRead(
            from_member_id=s["from_member_id"],
            from_member_name=member_names[s["from_member_id"]],
            to_member_id=s["to_member_id"],
            to_member_name=member_names[s["to_member_id"]],
            amount_cents=s["amount_cents"],
        )
        for s in settlements
    ]


def build_summary(trip: Trip, expenses: List[Expense]) -> TripSummaryRead:
    members_dicts = members_to_dicts(trip)
    expenses_dicts = expenses_to_dicts(expenses)
    participants_dicts = expense_participants_to_dicts(expenses)

    paid = calculate_total_paid_by_member(members_dicts, expenses_dicts)
    share = calculate_total_owed_share_by_member(
        members_dicts, expenses_dicts, participants_dicts
    )
    net = calculate_net_balance_by_member(
        members_dicts, expenses_dicts, participants_dicts
    )

    members_by_id = {m["id"]: m for m in members_dicts}
    total_spending = sum(e["amount_cents"] for e in expenses_dicts)

    highest_spender = None
    if members_dicts and any(paid.values()):
        highest_id = max(paid, key=paid.get)
        highest_spender = SummaryMemberMetric(
            name=members_by_id[highest_id]["name"], amount_cents=paid[highest_id]
        )

    highest_total_share = None
    if members_dicts and any(share.values()):
        share_id = max(share, key=share.get)
        highest_total_share = SummaryMemberMetric(
            name=members_by_id[share_id]["name"], amount_cents=share[share_id]
        )

    member_who_owes_most = None
    negative = {mid: bal for mid, bal in net.items() if bal < 0}
    if negative:
        owes_id = min(negative, key=negative.get)
        member_who_owes_most = SummaryMemberMetric(
            name=members_by_id[owes_id]["name"], amount_cents=abs(net[owes_id])
        )

    return TripSummaryRead(
        trip_name=trip.name,
        currency=trip.currency,
        total_trip_spending=total_spending,
        total_expenses=len(expenses_dicts),
        total_members=len(members_dicts),
        highest_spender=highest_spender,
        highest_total_share=highest_total_share,
        member_who_owes_most=member_who_owes_most,
    )


def create_expense_for_trip(
    db: Session, trip: Trip, payload: ExpenseCreate
) -> Expense:
    member_ids = trip_member_ids(trip)
    if payload.paid_by_member_id not in member_ids:
        raise HTTPException(
            status_code=422,
            detail="paid_by_member_id is not a member of this trip",
        )
    invalid = [m for m in payload.participant_ids if m not in member_ids]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"participant_ids not in trip: {invalid}",
        )

    expense = Expense(
        trip_id=trip.id,
        description=payload.description,
        amount_cents=payload.amount_cents,
        expense_date=payload.expense_date.isoformat(),
        paid_by_member_id=payload.paid_by_member_id,
        notes=payload.notes,
    )
    db.add(expense)
    db.flush()

    seen: set[int] = set()
    for pid in payload.participant_ids:
        if pid in seen:
            continue
        seen.add(pid)
        db.add(ExpenseParticipant(expense_id=expense.id, member_id=pid))

    db.commit()

    loaded = db.scalars(
        select(Expense)
        .where(Expense.id == expense.id)
        .options(
            selectinload(Expense.payer),
            selectinload(Expense.participants).selectinload(
                ExpenseParticipant.member
            ),
        )
    ).first()
    return loaded


def add_member_to_trip(db: Session, trip: Trip, payload: MemberAdd) -> Member:
    if payload.is_self:
        for member in trip.members:
            if member.is_self:
                raise HTTPException(
                    status_code=409,
                    detail="Trip already has a member marked as is_self",
                )

    member = Member(
        trip_id=trip.id,
        name=payload.name,
        is_self=1 if payload.is_self else 0,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


# ---------- Owner-authenticated routes ----------


@router.get("", response_model=List[TripRead])
def list_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Trip)
        .where(Trip.owner_user_id == current_user.id)
        .order_by(Trip.created_at.desc(), Trip.id.desc())
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=TripDetailRead, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trip = Trip(
        name=payload.name,
        currency=payload.currency,
        owner_user_id=current_user.id,
        share_token=generate_share_token(),
    )
    db.add(trip)
    db.flush()

    for member_data in payload.members:
        db.add(
            Member(
                trip_id=trip.id,
                name=member_data.name,
                is_self=1 if member_data.is_self else 0,
            )
        )
    db.commit()
    db.refresh(trip)
    return db.scalars(
        select(Trip)
        .where(Trip.id == trip.id)
        .options(selectinload(Trip.members))
    ).first()


@router.get("/{trip_id}", response_model=TripDetailRead)
def get_trip(trip: Trip = Depends(get_owned_trip)):
    return trip


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip: Trip = Depends(get_owned_trip), db: Session = Depends(get_db)
):
    db.delete(trip)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{trip_id}/rotate-share-token", response_model=TripRead
)
def rotate_share_token(
    trip: Trip = Depends(get_owned_trip), db: Session = Depends(get_db)
):
    trip.share_token = generate_share_token()
    db.commit()
    db.refresh(trip)
    return trip


# Members nested under trip


@router.post(
    "/{trip_id}/members",
    response_model=MemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    payload: MemberAdd,
    trip: Trip = Depends(get_owned_trip),
    db: Session = Depends(get_db),
):
    return add_member_to_trip(db, trip, payload)


@router.delete(
    "/{trip_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_member(
    member_id: int,
    trip: Trip = Depends(get_owned_trip),
    db: Session = Depends(get_db),
):
    member = db.scalars(
        select(Member).where(Member.id == member_id, Member.trip_id == trip.id)
    ).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    has_expense = db.scalars(
        select(Expense).where(Expense.paid_by_member_id == member_id)
    ).first()
    if has_expense is not None:
        raise HTTPException(
            status_code=409,
            detail="Cannot remove a member who has paid for expenses",
        )

    db.delete(member)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Expenses nested under trip


@router.post(
    "/{trip_id}/expenses",
    response_model=ExpenseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    payload: ExpenseCreate,
    trip: Trip = Depends(get_owned_trip),
    db: Session = Depends(get_db),
):
    expense = create_expense_for_trip(db, trip, payload)
    return serialize_expense(expense)


@router.get("/{trip_id}/expenses", response_model=List[ExpenseRead])
def list_expenses(
    payer_id: Optional[int] = None,
    date_from: Optional[str] = Query(default=None, alias="from"),
    date_to: Optional[str] = Query(default=None, alias="to"),
    trip: Trip = Depends(get_owned_trip),
    db: Session = Depends(get_db),
):
    expenses = load_expenses(db, trip.id, payer_id, date_from, date_to)
    return [serialize_expense(e) for e in expenses]


# Balances / settlements / summary


@router.get("/{trip_id}/balances", response_model=List[BalanceRead])
def get_balances(
    trip: Trip = Depends(get_owned_trip), db: Session = Depends(get_db)
):
    return build_balances(trip, load_expenses(db, trip.id))


@router.get("/{trip_id}/settlements", response_model=List[SettlementRead])
def get_settlements(
    trip: Trip = Depends(get_owned_trip), db: Session = Depends(get_db)
):
    return build_settlements(trip, load_expenses(db, trip.id))


@router.get("/{trip_id}/summary", response_model=TripSummaryRead)
def get_summary(
    trip: Trip = Depends(get_owned_trip), db: Session = Depends(get_db)
):
    return build_summary(trip, load_expenses(db, trip.id))


@router.get("/{trip_id}/expenses.csv")
def export_expenses(
    payer_id: Optional[int] = None,
    date_from: Optional[str] = Query(default=None, alias="from"),
    date_to: Optional[str] = Query(default=None, alias="to"),
    trip: Trip = Depends(get_owned_trip),
    db: Session = Depends(get_db),
):
    expenses = load_expenses(db, trip.id, payer_id, date_from, date_to)
    body, filename = build_csv(trip, expenses)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
