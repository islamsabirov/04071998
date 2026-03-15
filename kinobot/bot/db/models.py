from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vip_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    code_usages: Mapped[list["CodeUsage"]] = relationship("CodeUsage", back_populates="user")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="user")


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    channel_post_link: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    code_usages: Mapped[list["CodeUsage"]] = relationship("CodeUsage", back_populates="movie")


class CodeUsage(Base):
    __tablename__ = "code_usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.id"), nullable=False)
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="code_usages")
    movie: Mapped["Movie"] = relationship("Movie", back_populates="code_usages")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)       # tiyin (so'm * 100)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    # manual / payme / click
    method: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    # pending / approved / rejected / cancelled
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    # Payme / Click tomonidan berilgan tranzaksiya ID
    provider_txn_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="payments")


class RequiredChannel(Base):
    """Majburiy obuna kanallari (DB orqali boshqariladi)."""

    __tablename__ = "required_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    invite_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class BotAdmin(Base):
    """Bot orqali qo'shilgan adminlar (super-adminlar .env da)."""

    __tablename__ = "bot_admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    added_by: Mapped[int] = mapped_column(BigInteger, nullable=False)   # super-admin ID
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
