from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.metrics import metrics


class UserRateLimitMiddleware(BaseMiddleware):
    """Protects the free web service from accidental update floods."""

    def __init__(self, limit: int = 18, window_seconds: float = 5.0) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.events: dict[int, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)
        if not user:
            return await handler(event, data)

        now = monotonic()
        history = self.events[user.id]
        cutoff = now - self.window_seconds
        while history and history[0] < cutoff:
            history.popleft()
        if len(history) >= self.limit:
            metrics.increment("rate_limited")
            text = "So'rovlar juda tez yuborildi. Bir necha soniyadan keyin qayta urinib ko'ring."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=False)
            elif isinstance(event, Message):
                await event.answer(text)
            return None
        history.append(now)

        if len(self.events) > 5000:
            self.events = defaultdict(deque, {key: value for key, value in self.events.items() if value and value[-1] >= cutoff})
        return await handler(event, data)
