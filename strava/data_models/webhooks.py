from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class EventWebhook(BaseModel):
    model_config = ConfigDict(frozen=True)

    object_type: Literal["activity", "athlete"]
    object_id: int
    aspect_type: Literal["create", "update", "delete"]
    updates: dict[str, Any] | None = None
    owner_id: int
    subscription_id: int
    event_time: int
