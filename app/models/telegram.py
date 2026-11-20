from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TelegramLink(Base):
    __tablename__ = "telegram_links"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)


class TelegramCode(Base):
    __tablename__ = "telegram_codes"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[int]


class TelegramReceipt(Base):
    __tablename__ = "telegram_receipts"

    bot_username: Mapped[str] = mapped_column(String(32), primary_key=True)
    update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
