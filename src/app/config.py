import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field


class Settings(BaseModel):
    openai_api_key: Optional[str] = Field(
        default=None,
        description="API key for OpenAI-compatible service; required for live generation.",
    )
    model: str = Field(default="gpt-4o-mini", description="Model name for completion API.")
    data_path: str = Field(default="data/drug_facts.json", description="Path to drug facts JSON file.")
    top_k: int = Field(default=3, description="Number of documents to retrieve for grounding.")
    safety_template: str = Field(
        default=(
            "You are a medication information assistant. Provide concise, non-personalized information "
            "grounded in the provided documents. Include a disclaimer that this is not medical advice "
            "and users should consult a healthcare professional. Do not invent dosing details if not provided."
        ),
        description="System prompt for the model.",
    )

    class Config:
        frozen = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(openai_api_key=os.getenv("OPENAI_API_KEY"))
