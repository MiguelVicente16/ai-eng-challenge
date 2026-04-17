"""Pydantic shapes for admin-editable YAML configs.

Used by the `/api/config/*` routers to validate writes before touching
disk. Shapes match the YAML on-disk layout exactly so read+write is a
pass-through (no field renames).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ServiceRule(BaseModel):
    label: str
    dept_phone: str
    yes_rules: list[str] = Field(default_factory=list)
    no_rules: list[str] = Field(default_factory=list)


class ServicesConfig(BaseModel):
    services: dict[str, ServiceRule]


class PhrasesConfig(BaseModel):
    phrases: dict[str, str]


class _MetricBase(BaseModel):
    name: str
    description: str = ""


class StringMetric(_MetricBase):
    type: Literal["string"]
    max_length: int | None = None


class EnumMetric(_MetricBase):
    type: Literal["enum"]
    values: list[str]

    @field_validator("values")
    @classmethod
    def _non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("enum metric must have at least one value")
        return v


class ListMetric(_MetricBase):
    type: Literal["list"]
    item_type: Literal["string", "integer", "number"] = "string"
    max_items: int | None = None


class BooleanMetric(_MetricBase):
    type: Literal["boolean"]


class IntegerMetric(_MetricBase):
    type: Literal["integer"]
    min: int | None = None
    max: int | None = None


class NumberMetric(_MetricBase):
    type: Literal["number"]
    min: float | None = None
    max: float | None = None


Metric = StringMetric | EnumMetric | ListMetric | BooleanMetric | IntegerMetric | NumberMetric


class MetricsConfig(BaseModel):
    metrics: list[Metric]
