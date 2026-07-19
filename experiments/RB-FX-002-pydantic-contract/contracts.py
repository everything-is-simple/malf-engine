"""Pydantic is used only at the publication/viewer boundary in this trial."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CoordinateField(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    value: str | int | None
    reason_codes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def unknown_requires_reason(self):
        if self.value is None and not self.reason_codes:
            raise ValueError("None requires reason_codes")
        if self.value is not None and self.reason_codes:
            raise ValueError("known value cannot carry unknown reason_codes")
        return self


class Lineage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    run_id: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parser_version: str = Field(min_length=1)
    malf_rule_version: str = Field(min_length=1)
    adapter_version: str = Field(min_length=1)


class PublishedSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    schema_version: Literal["riskbench-snapshot-v0.1"]
    evaluation_date: date
    usage_level: Literal["verification_only", "research_only", "rejected"]
    price_line: Literal["raw_none", "qfq_back"]
    lineage: Lineage
    core: CoordinateField
    range: CoordinateField
