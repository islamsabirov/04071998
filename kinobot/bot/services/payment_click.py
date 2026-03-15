"""
Click (click.uz) to'lov tizimi integratsiyasi.

Endpoint: POST /click/
Ikki bosqich:
  action=0  — Prepare  (to'lovdan oldin)
  action=1  — Complete (muvaffaqiyatli to'lovdan keyin)

Imzo tekshiruvi (MD5):
  click_trans_id + service_id + SECRET_KEY + merchant_trans_id + amount + action + sign_time
"""

import hashlib
import logging

from aiohttp import web
from sqlalchemy import select

from bot.config import settings
from bot.db import AsyncSessionMaker
from bot.db.models import Payment, User
from bot.services.vip import set_vip

logger = logging.getLogger(__name__)

# Click xato kodlari
CLICK_OK = 0
CLICK_ERR_SIGN = -1
CLICK_ERR_INVALID_AMOUNT = -2
CLICK_ERR_ORDER_NOT_FOUND = -5
CLICK_ERR_ALREADY_PAID = -4
CLICK_ERR_FAILED = -9


def _sign(
    click_trans_id: str,
    service_id: str,
    merchant_trans_id: str,
    amount: str,
    action: str,
    sign_time: str,
) -> str:
    raw = (
        click_trans_id
        + service_id
        + settings.click_secret_key
        + merchant_trans_id
        + amount
        + action
        + sign_time
    )
    return hashlib.md5(raw.encode()).hexdigest()


async def click_handler(request: web.Request) -> web.Response:
    try:
        data = await request.post()
    except Exception:
        return web.json_response({"error": CLICK_ERR_FAILED, "error_note": "Bad request"})

    click_trans_id = data.get("click_trans_id", "")
    service_id = data.get("service_id", "")
    click_paydoc_id = data.get("click_paydoc_id", "")
    merchant_trans_id = data.get("merchant_trans_id", "")  # bizning payment.id
    amount = data.get("amount", "")
    action = data.get("action", "")
    error = data.get("error", "0")
    sign_time = data.get("sign_time", "")
    sign_string = data.get("sign_string", "")

    logger.info("Click action=%s merchant_trans_id=%s amount=%s", action, merchant_trans_id, amount)

    # Imzo tekshiruvi
    expected = _sign(click_trans_id, service_id, merchant_trans_id, amount, action, sign_time)
    if expected != sign_string:
        return web.json_response({
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "error": CLICK_ERR_SIGN,
            "error_note": "Noto'g'ri imzo",
        })

    try:
        payment_id = int(merchant_trans_id)
    except ValueError:
        return web.json_response({
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "error": CLICK_ERR_ORDER_NOT_FOUND,
            "error_note": "Buyurtma topilmadi",
        })

    async with AsyncSessionMaker() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if not payment:
            return web.json_response({
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "error": CLICK_ERR_ORDER_NOT_FOUND,
                "error_note": "Buyurtma topilmadi",
            })

        # Summa tekshiruvi (Click tiyin yuboradi)
        try:
            sent_amount = int(float(amount) * 100)
        except ValueError:
            sent_amount = 0

        if sent_amount != payment.amount:
            return web.json_response({
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "error": CLICK_ERR_INVALID_AMOUNT,
                "error_note": "Noto'g'ri summa",
            })

        if action == "0":
            # Prepare — faqat tekshirish
            if payment.status == "approved":
                return web.json_response({
                    "click_trans_id": click_trans_id,
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_prepare_id": payment.id,
                    "error": CLICK_ERR_ALREADY_PAID,
                    "error_note": "Allaqachon to'langan",
                })
            payment.provider_txn_id = click_trans_id
            await session.commit()
            return web.json_response({
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_prepare_id": payment.id,
                "error": CLICK_OK,
                "error_note": "Success",
            })

        elif action == "1":
            # Complete — to'lovni tasdiqlash
            if payment.status == "approved":
                return web.json_response({
                    "click_trans_id": click_trans_id,
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": payment.id,
                    "error": CLICK_ERR_ALREADY_PAID,
                    "error_note": "Allaqachon to'langan",
                })

            if error != "0":
                payment.status = "rejected"
                await session.commit()
                return web.json_response({
                    "click_trans_id": click_trans_id,
                    "merchant_trans_id": merchant_trans_id,
                    "merchant_confirm_id": payment.id,
                    "error": int(error),
                    "error_note": "To'lov bekor qilindi",
                })

            # VIP faollashtirish
            user_result = await session.execute(select(User).where(User.id == payment.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                await set_vip(session, user, payment.days)
                payment.status = "approved"
                await session.commit()

                try:
                    from bot.notify import notify_vip_activated
                    await notify_vip_activated(user.telegram_id, payment.days)
                except Exception:
                    pass

            return web.json_response({
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": payment.id,
                "error": CLICK_OK,
                "error_note": "Success",
            })

    return web.json_response({
        "click_trans_id": click_trans_id,
        "merchant_trans_id": merchant_trans_id,
        "error": CLICK_ERR_FAILED,
        "error_note": "Server xatosi",
    })
