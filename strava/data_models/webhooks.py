from typing import Any, Literal

from pydantic import BaseModel


class EventWebhook(BaseModel):
    object_type: Literal["activity", "athlete"]
    object_id: int
    aspect_type: Literal["create", "update", "delete"]
    updates: dict[str, Any] | None = None
    owner_id: int
    subscription_id: int
    event_time: int

    class Config:
        frozen = True
