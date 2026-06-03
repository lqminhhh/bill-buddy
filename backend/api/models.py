from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )

    trips: Mapped[List["Trip"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, server_default="USD")
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
    owner_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    share_token: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, unique=True, index=True
    )

    owner: Mapped[Optional["User"]] = relationship(back_populates="trips")
    members: Mapped[List["Member"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", order_by="Member.id"
    )
    expenses: Mapped[List["Expense"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )


class Member(Base):
    __tablename__ = "members"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_self: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    trip: Mapped["Trip"] = relationship(back_populates="members")


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    expense_date: Mapped[str] = mapped_column(String, nullable=False)
    paid_by_member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id"), nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    trip: Mapped["Trip"] = relationship(back_populates="expenses")
    payer: Mapped["Member"] = relationship(foreign_keys=[paid_by_member_id])
    participants: Mapped[List["ExpenseParticipant"]] = relationship(
        back_populates="expense", cascade="all, delete-orphan"
    )


class ExpenseParticipant(Base):
    __tablename__ = "expense_participants"

    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"), primary_key=True
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), primary_key=True
    )

    expense: Mapped["Expense"] = relationship(back_populates="participants")
    member: Mapped["Member"] = relationship()
