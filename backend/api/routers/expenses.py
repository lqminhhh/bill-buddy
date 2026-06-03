from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_owned_expense
from api.models import Expense, ExpenseParticipant, Member, Trip
from api.schemas import ExpenseRead, ExpenseUpdate
from api.serializers import serialize_expense

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


def _apply_expense_update(
    db: Session, expense: Expense, payload: ExpenseUpdate
) -> None:
    trip_member_ids = {
        m.id
        for m in db.scalars(
            select(Member).where(Member.trip_id == expense.trip_id)
        ).all()
    }

    if payload.paid_by_member_id is not None:
        if payload.paid_by_member_id not in trip_member_ids:
            raise HTTPException(
                status_code=422,
                detail="paid_by_member_id is not a member of this trip",
            )
        expense.paid_by_member_id = payload.paid_by_member_id

    if payload.participant_ids is not None:
        invalid = [m for m in payload.participant_ids if m not in trip_member_ids]
        if invalid:
            raise HTTPException(
                status_code=422,
                detail=f"participant_ids not in trip: {invalid}",
            )

    if payload.description is not None:
        expense.description = payload.description
    if payload.amount_cents is not None:
        expense.amount_cents = payload.amount_cents
    if payload.expense_date is not None:
        expense.expense_date = payload.expense_date.isoformat()
    if payload.notes is not None:
        expense.notes = payload.notes

    if payload.participant_ids is not None:
        for ep in list(expense.participants):
            db.delete(ep)
        db.flush()
        seen: set[int] = set()
        for pid in payload.participant_ids:
            if pid in seen:
                continue
            seen.add(pid)
            db.add(ExpenseParticipant(expense_id=expense.id, member_id=pid))


@router.get("/{expense_id}", response_model=ExpenseRead)
def get_expense(expense: Expense = Depends(get_owned_expense)):
    return serialize_expense(expense)


@router.patch("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    payload: ExpenseUpdate,
    expense: Expense = Depends(get_owned_expense),
    db: Session = Depends(get_db),
):
    _apply_expense_update(db, expense, payload)
    db.commit()
    db.refresh(expense)
    return serialize_expense(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense: Expense = Depends(get_owned_expense), db: Session = Depends(get_db)
):
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
