"""Pydantic schemas that validate user input."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

GOALS = ["weight loss", "muscle gain", "general wellness", "flexibility", "endurance"]
INTENSITIES = ["low", "medium", "high"]


class UserInput(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    user_id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    age: int = Field(ge=10, le=100)
    weight: float = Field(ge=20, le=300)
    goal: Literal["weight loss", "muscle gain", "general wellness", "flexibility", "endurance"]
    intensity: Literal["low", "medium", "high"]

    @field_validator("username", "user_id", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("goal", "intensity", mode="before")
    @classmethod
    def _normalize(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=40)
    feedback: str = Field(min_length=3, max_length=500)

    @field_validator("user_id", "feedback", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v
