from typing import Optional

from fastapi import Depends, HTTPException, Path, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from api.auth import decode_access_token
from api.database import get_db
from api.models import Expense, ExpenseParticipant, Trip, User


def _extract_bearer_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip() or None


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    token = _extract_bearer_token(request)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.scalars(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account no longer exists",
        )
    return user


def get_owned_trip(
    trip_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Trip:
    trip = db.scalars(
        select(Trip)
        .where(Trip.id == trip_id, Trip.owner_user_id == current_user.id)
        .options(selectinload(Trip.members))
    ).first()
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


def get_owned_expense(
    expense_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Expense:
    expense = db.scalars(
        select(Expense)
        .join(Trip, Trip.id == Expense.trip_id)
        .where(
            Expense.id == expense_id,
            Trip.owner_user_id == current_user.id,
        )
        .options(
            selectinload(Expense.payer),
            selectinload(Expense.participants).selectinload(
                ExpenseParticipant.member
            ),
        )
    ).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


def get_shared_trip(
    token: str = Path(...),
    db: Session = Depends(get_db),
) -> Trip:
    trip = db.scalars(
        select(Trip)
        .where(Trip.share_token == token)
        .options(selectinload(Trip.members))
    ).first()
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


def get_shared_expense(
    token: str,
    expense_id: int,
    db: Session = Depends(get_db),
) -> Expense:
    expense = db.scalars(
        select(Expense)
        .join(Trip, Trip.id == Expense.trip_id)
        .where(
            Expense.id == expense_id,
            Trip.share_token == token,
        )
        .options(
            selectinload(Expense.payer),
            selectinload(Expense.participants).selectinload(
                ExpenseParticipant.member
            ),
        )
    ).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense
