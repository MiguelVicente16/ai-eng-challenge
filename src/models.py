"""Domain models for the customer support system."""

from pydantic import BaseModel


class Customer(BaseModel):
    """A bank customer with identity and secret question data."""

    name: str
    phone: str
    iban: str
    secret: str
    answer: str


class Account(BaseModel):
    """A bank account with premium status."""

    iban: str
    premium: bool = False
