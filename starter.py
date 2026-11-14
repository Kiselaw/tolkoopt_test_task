"""Решение для Python 3.11+: используется asyncio.timeout.

Запуск примера: python starter.py
Запуск тестов: python -m pytest -q starter.py
"""

import asyncio
import logging
from decimal import Decimal, ROUND_DOWN
from typing import Any, Callable, Coroutine, TypedDict


logger = logging.getLogger(__name__)


class Offer(TypedDict):
    seller: str
    price: Decimal
    delivery_days: int | None


class OffersResponse(TypedDict):
    status: str
    offers: list[Offer]


class InvalidStatusError(Exception):
    pass


async def recommend_price(
    fetch_offers: Callable[[], Coroutine[Any, Any, OffersResponse]],
    current_price: Decimal,
    min_price: Decimal,
    timeout_s: float = 2.0,
) -> dict[str, str | Decimal]:
    """Рассчитать новую цену на основе предложений конкурентов."""
    try:
        async with asyncio.timeout(timeout_s):
            result = await fetch_offers()
        if result["status"] != "success":
            raise InvalidStatusError(f"Статус источника: {result['status']!r}; ожидается 'success'")
    except asyncio.TimeoutError:
        logger.error("Время ожидания выполнения fetch_offers превышено")
        return {"price": current_price, "decision": "HOLD", "reason": "Не удалось получить новые данные"}
    except InvalidStatusError as error:
        logger.error("Статус при получении новых данных не 'success'")
        return {"price": current_price, "decision": "HOLD", "reason": "Статус при получении новых данных не 'success'"}
    except Exception as e:
        logger.error(f"Ошибка при получении предложений конкурентов: {repr(e)}")
        return {"price": current_price, "decision": "HOLD", "reason": "Не удалось получить новые данные"}

    prices = [
        offer["price"]
        for offer in result["offers"]
        if (
            offer["delivery_days"] is not None
            and offer["delivery_days"] <= 6
            and offer["seller"].lower() != "myshop"
        )
    ]
    if prices:
        discounted_price = (min(prices) * Decimal("0.985")).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )
        price = max(min_price, discounted_price)
        if (
            price > current_price + current_price * Decimal("0.30")
            or price < current_price - current_price * Decimal("0.30")
        ):
            return {"price": price, "decision": "REVIEW", "reason": "Найдена минимальная цена, но требуется ревью"}
        return {"price": price, "decision": "APPLY", "reason": "Найдена минимальная цена"}
    else:
        return {"price": current_price, "decision": "HOLD", "reason": "Нет подходящих предложений конкурентов"}


async def sample_fetch_offers() -> OffersResponse:
    """Вернуть пример предложений."""
    return {
        "status": "success",
        "offers": [
            {"seller": "myshop", "price": Decimal("4300.00"), "delivery_days": 2},
            {"seller": "PARTS", "price": Decimal("4800.00"), "delivery_days": 3},
            {"seller": "SLOW", "price": Decimal("4700.00"), "delivery_days": 8},
        ],
    }


def test_recommend_price_calculates_price():
    """Должен отфильтровать предложения и округлить скидку вниз до копейки."""
    async def fetch_offers() -> OffersResponse:
        return {
            "status": "success",
            "offers": [
                {"seller": "MyShOp", "price": Decimal("50.00"), "delivery_days": 2},
                {"seller": "PARTS", "price": Decimal("100.01"), "delivery_days": 6},
                {"seller": "OTHER", "price": Decimal("110.00"), "delivery_days": 3},
                {"seller": "SLOW", "price": Decimal("40.00"), "delivery_days": 7},
                {"seller": "UNKNOWN", "price": Decimal("30.00"), "delivery_days": None},
            ],
        }

    result = asyncio.run(recommend_price(
        fetch_offers,
        current_price=Decimal("100.00"),
        min_price=Decimal("90.00"),
    ))

    assert isinstance(result["price"], Decimal)
    assert result["price"] == Decimal("98.50")
    assert result["decision"] == "APPLY"


def test_recommend_price_holds_on_invalid_status():
    """Должен сохранить текущую цену даже ниже минимума при ошибочном статусе."""
    async def fetch_offers() -> OffersResponse:
        return {
            "status": "error",
            "offers": [
                {"seller": "PARTS", "price": Decimal("100.00"), "delivery_days": 3},
            ],
        }

    result = asyncio.run(recommend_price(
        fetch_offers,
        current_price=Decimal("80.00"),
        min_price=Decimal("90.00"),
    ))

    assert isinstance(result["price"], Decimal)
    assert result["price"] == Decimal("80.00")
    assert result["decision"] == "HOLD"


if __name__ == "__main__":
    print(asyncio.run(recommend_price(
        sample_fetch_offers,
        current_price=Decimal("4900.00"),
        min_price=Decimal("4500.00"),
    )))
