"""
Payme (paycom.uz) to'lov tizimi integratsiyasi.

Endpoint: POST /payme/
Basic Auth: "Paycom:{PAYME_KEY}" base64

JSONRPC metodlar:
  CheckPerformTransaction  — to'lovni amalga oshirish mumkinligini tekshirish
  CreateTransaction        — tranzaksiya yaratish
  PerformTransaction       — to'lovni tasdiqlash
  CancelTransaction        — to'lovni bekor qilish
  CheckTransaction         — tranzaksiya holatini tekshirish
  GetStatement             — hisobot

amount Payme'dan TIYIN keladi (1 so'm = 100 tiyin).
Payment.amount ham TIYIN saqlanadi.
"""

import base64
import json
import logging
from datetime import datetime, timezone

from aiohttp import web
from sqlalchemy import select

from bot.config import settings
from bot.db import AsyncSessionMaker
from bot.db.models import Payment, User
from bot.services.vip import set_vip

logger = logging.getLogger(__name__)

# ── Payme xato kodlari ──────────────────────────────────────────
ERR_INVALID_AMOUNT = {"code": -31001, "message": {"uz": "Noto'g'ri summa"}}
ERR_TRANSACTION_NOT_FOUND = {"code": -31003, "message": {"uz": "Tranzaksiya topilmadi"}}
ERR_INVALID_ACCOUNT = {"code": -31050, "message": {"uz": "Buyurtma topilmadi"}}
ERR_COULD_NOT_PERFORM = {"code": -31008, "message": {"uz": "To'lovni amalga oshirib bo'lmadi"}}
ERR_ALREADY_DONE = {"code": -31060, "message": {"uz": "Tranzaksiya allaqachon bajarilgan"}}
ERR_UNABLE_TO_CANCEL = {"code": -31007, "message": {"uz": "Bekor qilib bo'lmaydi"}}

# Tranzaksiya holatlari
STATE_PENDING = 1
STATE_COMPLETED = 2
STATE_CANCELLED = -1
STATE_CANCEL_AFTER_COMPLETE = -2


def _check_auth(request: web.Request) -> bool:
    """Basic Auth tekshiruvi."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth[6:]).decode()
        _, key = decoded.split(":", 1)
        return key == settings.payme_key
    except Exception:
        return False


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


async def payme_handler(request: web.Request) -> web.Response:
    if not _check_auth(request):
        return web.json_response(
            {"error": {"code": -32504, "message": "Unauthorized"}}, status=401
        )

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": {"code": -32700, "message": "Parse error"}})

    method = body.get("method", "")
    params = body.get("params", {})
    rpc_id = body.get("id", 1)

    logger.info("Payme RPC: %s | params: %s", method, params)

    handlers = {
        "CheckPerformTransaction": _check_perform,
        "CreateTransaction": _create_transaction,
        "PerformTransaction": _perform_transaction,
        "CancelTransaction": _cancel_transaction,
        "CheckTransaction": _check_transaction,
        "GetStatement": _get_statement,
    }

    handler = handlers.get(method)
    if not handler:
        return web.json_response(
            {"id": rpc_id, "error": {"code": -32601, "message": "Method not found"}}
        )

    result, error = await handler(params)
    if error:
        return web.json_response({"id": rpc_id, "error": error})
    return web.json_response({"id": rpc_id, "result": result})


async def _get_payment(params: dict) -> Payment | None:
    account = params.get("account", {})
    try:
        payment_id = int(account.get("order_id", 0))
    except (ValueError, TypeError):
        return None
    async with AsyncSessionMaker() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()


async def _check_perform(params: dict) -> tuple[dict | None, dict | None]:
    payment = await _get_payment(params)
    if not payment:
        return None, ERR_INVALID_ACCOUNT

    amount = params.get("amount", 0)
    if amount != payment.amount:
        return None, ERR_INVALID_AMOUNT

    if payment.status not in ("pending",):
        return None, ERR_COULD_NOT_PERFORM

    return {"allow": True}, None


async def _create_transaction(params: dict) -> tuple[dict | None, dict | None]:
    payment = await _get_payment(params)
    if not payment:
        return None, ERR_INVALID_ACCOUNT

    amount = params.get("amount", 0)
    if amount != payment.amount:
        return None, ERR_INVALID_AMOUNT

    txn_id = str(params.get("id", ""))
    time_ms = params.get("time", _now_ms())

    async with AsyncSessionMaker() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment.id))
        p = result.scalar_one()

        if p.provider_txn_id and p.provider_txn_id != txn_id:
            return None, ERR_COULD_NOT_PERFORM

        if p.status == "approved":
            return None, ERR_ALREADY_DONE

        if p.status == "rejected":
            return None, ERR_COULD_NOT_PERFORM

        p.provider_txn_id = txn_id
        await session.commit()

    return {
        "create_time": time_ms,
        "transaction": str(payment.id),
        "state": STATE_PENDING,
    }, None


async def _perform_transaction(params: dict) -> tuple[dict | None, dict | None]:
    txn_id = str(params.get("id", ""))

    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Payment).where(Payment.provider_txn_id == txn_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            return None, ERR_TRANSACTION_NOT_FOUND

        if payment.status == "approved":
            return {
                "transaction": str(payment.id),
                "perform_time": _now_ms(),
                "state": STATE_COMPLETED,
            }, None

        if payment.status != "pending":
            return None, ERR_COULD_NOT_PERFORM

        # VIP faollashtirish
        user_result = await session.execute(select(User).where(User.id == payment.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            await set_vip(session, user, payment.days)
            payment.status = "approved"
            await session.commit()

            # Foydalanuvchiga xabar berish (bot instance kerak emas, task orqali)
            try:
                from bot.notify import notify_vip_activated
                await notify_vip_activated(user.telegram_id, payment.days)
            except Exception:
                pass

    return {
        "transaction": str(payment.id),
        "perform_time": _now_ms(),
        "state": STATE_COMPLETED,
    }, None


async def _cancel_transaction(params: dict) -> tuple[dict | None, dict | None]:
    txn_id = str(params.get("id", ""))

    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Payment).where(Payment.provider_txn_id == txn_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            return None, ERR_TRANSACTION_NOT_FOUND

        if payment.status == "approved":
            return None, ERR_UNABLE_TO_CANCEL

        payment.status = "rejected"
        await session.commit()

    return {
        "transaction": str(payment.id),
        "cancel_time": _now_ms(),
        "state": STATE_CANCELLED,
    }, None


async def _check_transaction(params: dict) -> tuple[dict | None, dict | None]:
    txn_id = str(params.get("id", ""))

    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Payment).where(Payment.provider_txn_id == txn_id)
        )
        payment = result.scalar_one_or_none()

    if not payment:
        return None, ERR_TRANSACTION_NOT_FOUND

    state_map = {
        "pending": STATE_PENDING,
        "approved": STATE_COMPLETED,
        "rejected": STATE_CANCELLED,
    }
    state = state_map.get(payment.status, STATE_CANCELLED)

    return {
        "create_time": int(payment.created_at.timestamp() * 1000),
        "perform_time": int(payment.created_at.timestamp() * 1000) if payment.status == "approved" else 0,
        "cancel_time": 0,
        "transaction": str(payment.id),
        "state": state,
        "reason": None,
    }, None


async def _get_statement(params: dict) -> tuple[dict | None, dict | None]:
    from_ms = params.get("from", 0)
    to_ms = params.get("to", _now_ms())

    from_dt = datetime.fromtimestamp(from_ms / 1000, tz=timezone.utc)
    to_dt = datetime.fromtimestamp(to_ms / 1000, tz=timezone.utc)

    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.method == "payme",
                Payment.created_at >= from_dt,
                Payment.created_at <= to_dt,
            )
        )
        payments = result.scalars().all()

    transactions = []
    for p in payments:
        state_map = {"pending": STATE_PENDING, "approved": STATE_COMPLETED, "rejected": STATE_CANCELLED}
        transactions.append({
            "id": p.provider_txn_id or str(p.id),
            "time": int(p.created_at.timestamp() * 1000),
            "amount": p.amount,
            "account": {"order_id": str(p.id)},
            "create_time": int(p.created_at.timestamp() * 1000),
            "perform_time": int(p.created_at.timestamp() * 1000) if p.status == "approved" else 0,
            "cancel_time": 0,
            "transaction": str(p.id),
            "state": state_map.get(p.status, STATE_CANCELLED),
            "reason": None,
        })

    return {"transactions": transactions}, None
