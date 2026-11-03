"""Request and response shapes. The model's output must validate against Triage, or the request fails."""
from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    connectivity = "connectivity"        # app can't reach the vehicle: Bluetooth, pairing, telematics, sync
    app_bug = "app_bug"                  # crashes, freezes, wrong screens, display errors in the app
    navigation = "navigation"            # routes, maps, turn-by-turn directions, trip planning
    account = "account"                  # login, password, subscription, billing, personal data
    safety = "safety"                    # crash or fall detection, emergency call, anything about rider safety
    feedback = "feedback"                # feature requests, praise, general opinions


class Urgency(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Language(str, Enum):
    de = "de"
    en = "en"


class TicketIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class Triage(BaseModel):
    category: Category
    urgency: Urgency
    language: Language
    summary: str = Field(min_length=1, max_length=200, description="One sentence in English")


class TriageResponse(Triage):
    model: str
    latency_ms: int
