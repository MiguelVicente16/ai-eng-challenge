"""Simulate a phone call to the DEUS Bank customer support system.

Usage:
    uv run python scripts/simulate_call.py                      # Lisa premium (default)
    uv run python scripts/simulate_call.py --scenario marco     # Marco regular
    uv run python scripts/simulate_call.py --scenario unknown   # Non-customer
    uv run python scripts/simulate_call.py --scenario retry     # Retry exhaustion
    uv run python scripts/simulate_call.py --scenario all       # Every scenario
    uv run python scripts/simulate_call.py --interactive        # You type each turn

Requires the API to be running: `make run` in another terminal.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field

import httpx

BASE_URL = "http://localhost:8000"

GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


@dataclass
class Turn:
    message: str
    label: str = ""


@dataclass
class Scenario:
    name: str
    description: str
    caller_phone: str | None
    turns: list[Turn] = field(default_factory=list)


SCENARIOS: dict[str, Scenario] = {
    "lisa": Scenario(
        name="Lisa — premium, known caller",
        description="Lisa calls from a recognized number and asks about yacht insurance.",
        caller_phone="+1122334455",
        turns=[
            Turn("", "call opens"),
            Turn("I need help with my yacht insurance", "states problem"),
            Turn("My name is Lisa and my IBAN is DE89370400440532013000", "provides identity"),
            Turn("Yoda", "answers secret"),
        ],
    ),
    "marco": Scenario(
        name="Marco — regular, unknown caller",
        description="Marco calls without caller ID and asks about a mortgage.",
        caller_phone=None,
        turns=[
            Turn("", "call opens"),
            Turn("I want to apply for a mortgage", "states problem"),
            Turn("I am Marco and my phone is +5566778899", "provides identity"),
            Turn("Blue", "answers secret"),
        ],
    ),
    "unknown": Scenario(
        name="Unknown — not a DEUS customer",
        description="A stranger tries to call and fails identity verification.",
        caller_phone=None,
        turns=[
            Turn("", "call opens"),
            Turn("I need help with my account", "states problem"),
            Turn("I'm John at +0000000000", "provides wrong identity"),
        ],
    ),
    "retry": Scenario(
        name="Retry exhaustion on problem capture",
        description="Caller gives unclear problem twice and is transferred to general support.",
        caller_phone="+1122334455",
        turns=[
            Turn("", "call opens"),
            Turn("uh", "unclear 1"),
            Turn("", "unclear 2 → fallback"),
        ],
    ),
}


def _banner(scenario: Scenario) -> None:
    print()
    print(BOLD + "─" * 78 + RESET)
    print(f"{BOLD}📞  {scenario.name}{RESET}")
    print(f"{DIM}{scenario.description}{RESET}")
    if scenario.caller_phone:
        print(f"{DIM}Caller ID: {scenario.caller_phone}{RESET}")
    print(BOLD + "─" * 78 + RESET)
    print()


def _print_turn(num: int, label: str, user: str, agent: str, elapsed: float) -> None:
    tag = f" — {label}" if label else ""
    print(f"{BOLD}Turn {num}{tag}{RESET} {DIM}({elapsed:.2f}s){RESET}")
    if user:
        print(f"{BLUE}  ▸ user:  {user}{RESET}")
    else:
        print(f"{DIM}  ▸ user:  (call opened, no audio yet){RESET}")
    print(f"{GREEN}  ◂ agent: {agent}{RESET}")
    print()


def _health_check(client: httpx.Client) -> None:
    try:
        client.get("/api/health").raise_for_status()
    except httpx.HTTPError as exc:
        print(f"{YELLOW}❌ Server not reachable at {BASE_URL}: {exc}{RESET}")
        print(f"{YELLOW}   Start it with `make run` in another terminal first.{RESET}")
        sys.exit(1)


def run_scripted(scenario: Scenario) -> None:
    _banner(scenario)

    session_id: str | None = None
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        _health_check(client)

        for i, turn in enumerate(scenario.turns, start=1):
            payload: dict[str, object] = {"message": turn.message}
            if session_id:
                payload["session_id"] = session_id
            elif scenario.caller_phone:
                payload["caller_phone"] = scenario.caller_phone

            start = time.perf_counter()
            try:
                response = client.post("/chat", json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                print(f"{YELLOW}❌ Request failed: {exc}{RESET}")
                if hasattr(exc, "response") and exc.response is not None:
                    print(f"{YELLOW}   {exc.response.text}{RESET}")
                sys.exit(1)

            elapsed = time.perf_counter() - start
            data = response.json()
            session_id = data["session_id"]
            _print_turn(i, turn.label, turn.message, data["response"], elapsed)

    print(f"{DIM}Session ended — session_id={session_id}{RESET}")
    print()


def run_interactive(caller_phone: str | None) -> None:
    print()
    print(BOLD + "─" * 78 + RESET)
    print(f"{BOLD}📞  Interactive mode{RESET}")
    if caller_phone:
        print(f"{DIM}Caller ID: {caller_phone}{RESET}")
    print(f"{DIM}Type 'exit' or press Ctrl-C to hang up.{RESET}")
    print(BOLD + "─" * 78 + RESET)
    print()

    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        _health_check(client)

        payload: dict[str, object] = {"message": ""}
        if caller_phone:
            payload["caller_phone"] = caller_phone

        data = client.post("/chat", json=payload).json()
        session_id = data["session_id"]
        print(f"{GREEN}agent: {data['response']}{RESET}\n")

        while True:
            try:
                msg = input(f"{BLUE}you:   {RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if msg.lower() in {"exit", "quit"}:
                break

            start = time.perf_counter()
            data = client.post("/chat", json={"message": msg, "session_id": session_id}).json()
            elapsed = time.perf_counter() - start
            print(f"{GREEN}agent: {data['response']}{RESET} {DIM}({elapsed:.2f}s){RESET}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a phone call to DEUS Bank")
    parser.add_argument(
        "--scenario",
        "-s",
        choices=[*SCENARIOS.keys(), "all"],
        default="lisa",
        help="Scripted scenario to run (default: lisa). 'all' runs every scenario.",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive mode — type each user message yourself.",
    )
    parser.add_argument(
        "--caller-phone",
        help="Caller phone number (interactive mode only)",
    )
    args = parser.parse_args()

    if args.interactive:
        run_interactive(args.caller_phone)
        return

    if args.scenario == "all":
        for scenario in SCENARIOS.values():
            run_scripted(scenario)
    else:
        run_scripted(SCENARIOS[args.scenario])


if __name__ == "__main__":
    main()
