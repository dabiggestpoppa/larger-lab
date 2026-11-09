"""One worked B6-I1 request, runnable offline and deterministic.

    python oce/sdk/examples/one_worked_request.py
"""
from __future__ import annotations

import itertools
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from oce.sdk.client import Client  # noqa: E402


def main() -> int:
    client = Client(actor="actor-1")
    receipt = client.submit_intent("summarise the open evidence item")
    print(json.dumps({"operation": "oce.sdk.intents.submit", "receipt": receipt},
                     sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
