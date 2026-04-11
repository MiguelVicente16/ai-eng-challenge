"""Seed customer and account data for the bank support system."""

from src.models import Account, Customer

CUSTOMERS: list[Customer] = [
    Customer(
        name="Lisa",
        phone="+1122334455",
        iban="DE89370400440532013000",
        secret="Which is the name of my dog?",
        answer="Yoda",
    ),
    Customer(
        name="Marco",
        phone="+5566778899",
        iban="DE75512108001245126199",
        secret="What is my favorite color?",
        answer="Blue",
    ),
    Customer(
        name="Sophie",
        phone="+3344556677",
        iban="DE12500105170648489890",
        secret="What city was I born in?",
        answer="Berlin",
    ),
]

ACCOUNTS: list[Account] = [
    Account(iban="DE89370400440532013000", premium=True),
    Account(iban="DE75512108001245126199", premium=False),
    Account(iban="DE12500105170648489890", premium=True),
]
