"""Decision playbook domain models."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class DecisionPlaybook(BaseModel):
    id: str = Field(..., description="Unique identifier.")
    name: str = Field(..., description="Human readable name.")
    description: str = Field(..., description="Purpose of the playbook.")
    version: str = Field("1.0.0", description="Semantic version.")
    prompt_guidelines: str = Field(..., description="Prompt additions passed to the compiler LLM.")
    keywords: List[str] = Field(default_factory=list, description="Goal keywords to match.")
    tags: List[str] = Field(default_factory=list, description="Additional classification metadata.")

