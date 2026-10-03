#!/usr/bin/env python3
"""OCE Local Ground — unit tests for the portable `docker compose ps`
parser (B1-LOCAL, A-003). Every documented output form is covered:
a single JSON array, a single JSON object, and newline-delimited JSON
objects. Malformed or incomplete output must be rejected clearly.
"""
import json

import pytest

from oce_compose import parse_compose_ps, published_ports

SVC_A = {"Service": "postgresql", "Name": "oce-local-postgresql",
         "State": "running", "Health": "healthy", "Publishers": None}
SVC_B = {"Service": "redis", "Name": "oce-local-redis",
         "State": "running", "Health": "healthy", "Publishers": None}


def test_parses_json_array():
    text = json.dumps([SVC_A, SVC_B])
    entries = parse_compose_ps(text)
    assert [e["Service"] for e in entries] == ["postgresql", "redis"]


def test_parses_single_json_object():
    text = json.dumps(SVC_A)
    entries = parse_compose_ps(text)
    assert len(entries) == 1 and entries[0]["Service"] == "postgresql"


def test_parses_ndjson_lines():
    text = json.dumps(SVC_A) + "\n" + json.dumps(SVC_B) + "\n"
    entries = parse_compose_ps(text)
    assert len(entries) == 2


def test_parses_empty_output():
    assert parse_compose_ps("") == []
    assert parse_compose_ps("\n  \n") == []


def test_rejects_malformed_output():
    with pytest.raises(ValueError):
        parse_compose_ps("this is not json at all")


def test_rejects_incomplete_array():
    with pytest.raises(ValueError):
        parse_compose_ps("[{\"Service\": \"postgresql\"")  # truncated array


def test_rejects_malformed_ndjson_line():
    with pytest.raises(ValueError):
        parse_compose_ps("{\"Service\": \"postgresql\"}\n{broken\n")


def test_rejects_non_object_array_entry():
    with pytest.raises(ValueError):
        parse_compose_ps("[42]")


def test_published_ports_detected():
    bad = {"Service": "leaky", "Name": "x", "Publishers": [{"TargetPort": 5432}]}
    good = {"Service": "postgresql", "Name": "y", "Publishers": None}
    assert published_ports([bad, good]) == ["leaky"]


def test_legacy_ports_string_detected():
    legacy = {"Service": "leaky", "Name": "z", "Ports": "0.0.0.0:5432->5432/tcp"}
    none_legacy = {"Service": "redis", "Name": "r", "Ports": ""}
    assert published_ports([legacy, none_legacy]) == ["leaky"]
