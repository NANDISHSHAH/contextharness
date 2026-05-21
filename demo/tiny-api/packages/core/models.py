"""Shared domain models for Tiny API."""

from dataclasses import dataclass


@dataclass
class User:
    id: str
    email: str


@dataclass
class Invoice:
    id: str
    user_id: str
    amount_cents: int
