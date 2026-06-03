from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_shared_expense, get_shared_trip
from api.models import Expense, Trip
from api.routers.expenses import _apply_expense_update
from api.routers.trips import (
    add_member_to_trip,
    build_balances,
    build_csv,
    build_settlements,
    build_summary,
    create_expense_for_trip,
    load_expenses,
)
from api.schemas import (
    BalanceRead,
    ExpenseCreate,
    ExpenseRead,
    ExpenseUpdate,
    MemberAdd,
    MemberRead,
    SettlementRead,
    TripDetailRead,
    TripSummaryRead,
)
from api.serializers import serialize_expense

router = APIRouter(prefix="/api/share/{token}", tags=["share"])


@router.get("", response_model=TripDetailRead)
def get_shared_trip_detail(trip: Trip = Depends(get_shared_trip)):
    return trip


@router.get("/expenses", response_model=List[ExpenseRead])
def list_shared_expenses(
    payer_id: Optional[int] = None,
    date_from: Optional[str] = Query(default=None, alias="from"),
    date_to: Optional[str] = Query(default=None, alias="to"),
    trip: Trip = Depends(get_shared_trip),
    db: Session = Depends(get_db),
):
    expenses = load_expenses(db, trip.id, payer_id, date_from, date_to)
    return [serialize_expense(e) for e in expenses]


@router.post(
    "/expenses",
    response_model=ExpenseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_shared_expense(
    payload: ExpenseCreate,
    trip: Trip = Depends(get_shared_trip),
    db: Session = Depends(get_db),
):
    expense = create_expense_for_trip(db, trip, payload)
    return serialize_expense(expense)


@router.patch("/expenses/{expense_id}", response_model=ExpenseRead)
def update_shared_expense(
    payload: ExpenseUpdate,
    expense: Expense = Depends(get_shared_expense),
    db: Session = Depends(get_db),
):
    _apply_expense_update(db, expense, payload)
    db.commit()
    db.refresh(expense)
    return serialize_expense(expense)


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shared_expense(
    expense: Expense = Depends(get_shared_expense),
    db: Session = Depends(get_db),
):
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/members",
    response_model=MemberRead,
    status_code=status.HTTP_201_CREATED,
)
def add_shared_member(
    payload: MemberAdd,
    trip: Trip = Depends(get_shared_trip),
    db: Session = Depends(get_db),
):
    return add_member_to_trip(db, trip, payload)


@router.get("/balances", response_model=List[BalanceRead])
def get_shared_balances(
    trip: Trip = Depends(get_shared_trip), db: Session = Depends(get_db)
):
    return build_balances(trip, load_expenses(db, trip.id))


@router.get("/settlements", response_model=List[SettlementRead])
def get_shared_settlements(
    trip: Trip = Depends(get_shared_trip), db: Session = Depends(get_db)
):
    return build_settlements(trip, load_expenses(db, trip.id))


@router.get("/summary", response_model=TripSummaryRead)
def get_shared_summary(
    trip: Trip = Depends(get_shared_trip), db: Session = Depends(get_db)
):
    return build_summary(trip, load_expenses(db, trip.id))


@router.get("/expenses.csv")
def export_shared_expenses(
    payer_id: Optional[int] = None,
    date_from: Optional[str] = Query(default=None, alias="from"),
    date_to: Optional[str] = Query(default=None, alias="to"),
    trip: Trip = Depends(get_shared_trip),
    db: Session = Depends(get_db),
):
    expenses = load_expenses(db, trip.id, payer_id, date_from, date_to)
    body, filename = build_csv(trip, expenses)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
