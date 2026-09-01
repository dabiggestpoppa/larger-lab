"""SENSOR-B4-I02 — content-addressed keys and path-encoding tests.

Proves: blob key ab/cd partitioning + encoding suffixes; content ID immune to
provider/sensor/instrument; deterministic reversible escaping with no
traversal/collision; Unicode identity without normalization; projection
logical path derivation with explicit date components; lexical root
containment with zero filesystem mutation; OS-independent canonical keys.
"""

from __future__ import annotations

from typing import Any

import pytest

from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.paths import (
    blob_object_key,
    escape_path_segment,
    projection_object_key,
    resolve_under_root,
    unescape_path_segment,
)

# "abcdef0123456789" x4 == 64 lowercase hex chars.  h0h1="ab", h2h3="cd".
DIGEST = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"

_PROJECTION_KW: dict[str, Any] = {
    "provider": "kraken_futures",
    "venue": "kraken",
    "sensor_family": "MECHANICAL_LIQUIDATION",
    "native_instrument": "PI_XBTUSD",
    "native_granularity": "1h",
    "year": 2026,
    "month": 8,
    "day": 31,
    "schema_key": "liquidation_volume",
    "shard_id": 0,
    "projection_sha256": DIGEST,
}


class TestBlobObjectKey:
    def test_exact_layout_none(self) -> None:
        assert (
            blob_object_key(DIGEST, StorageEncoding.NONE)
            == f"blobs/sha256/ab/cd/{DIGEST}.blob"
        )

    def test_exact_layout_zstd(self) -> None:
        assert (
            blob_object_key(DIGEST, StorageEncoding.ZSTD)
            == f"blobs/sha256/ab/cd/{DIGEST}.blob.zst"
        )

    def test_no_off_by_one_slicing(self) -> None:
        # h0h1 = FIRST two chars, h2h3 = NEXT two — never shifted.
        key = blob_object_key(DIGEST, StorageEncoding.NONE)
        assert key.startswith("blobs/sha256/ab/cd/")
        assert key.split("/")[-1] == f"{DIGEST}.blob"

    def test_wrapper_encoding_changes_suffix_only_not_content_id(self) -> None:
        none_key = blob_object_key(DIGEST, StorageEncoding.NONE)
        zstd_key = blob_object_key(DIGEST, StorageEncoding.ZSTD)
        assert none_key.removesuffix(".blob") == zstd_key.removesuffix(".blob.zst")
        assert none_key.endswith(".blob")
        assert zstd_key.endswith(".blob.zst")
        # The content ID (the full digest) appears identically in both keys.
        assert f"/{DIGEST}" in none_key and f"/{DIGEST}" in zstd_key

    def test_no_provider_sensor_instrument_components(self) -> None:
        key = blob_object_key(DIGEST, StorageEncoding.NONE)
        for forbidden in ("provider", "sensor", "instrument", "venue", "date"):
            assert forbidden not in key

    def test_malformed_digests_rejected(self) -> None:
        malformed = [
            DIGEST[:63],           # 63 chars
            DIGEST + "0",          # 65 chars
            DIGEST.upper(),        # uppercase
            "g" + DIGEST[1:],      # nonhex
            " " + DIGEST[1:],      # whitespace
            "sha256:" + DIGEST,    # prefix
            "ab/cd/" + DIGEST,     # path-containing value
        ]
        for bad in malformed:
            with pytest.raises(ValueError):
                blob_object_key(bad, StorageEncoding.NONE)

    def test_invalid_encoding_rejected(self) -> None:
        with pytest.raises(TypeError):
            blob_object_key(DIGEST, "NONE")  # type: ignore[arg-type]


class TestEscapeRoundTrip:
    @pytest.mark.parametrize(
        "value",
        [
            "BTC/USDT",
            "BTC-USDT",
            "btc-usdt",
            "BTC USDT",
            "PI_XBTUSD",
            "..",
            "../x",
            "x/../y",
            "/x",
            "\\",
            "..\\x",
            "%",
            "%2F",
            ".",
            "...",
            "héllo-世界",
            "sp ace=eq",
            "a\x00b",
        ],
    )
    def test_round_trip(self, value: str) -> None:
        encoded = escape_path_segment(value)
        assert unescape_path_segment(encoded) == value

    def test_no_traversal_in_encoded_output(self) -> None:
        for value in ("..", "../x", "x/../y", "/x", "\\", "..\\x"):
            encoded = escape_path_segment(value)
            assert "/" not in encoded and "\\" not in encoded
            assert encoded != ".."
            assert ".." not in encoded.split("/")

    def test_safe_alphabet_left_literal(self) -> None:
        assert escape_path_segment("abc_-XYZ012") == "abc_-XYZ012"

    def test_collision_resistance(self) -> None:
        pairs = [("/", "%2F"), (".", "%2E"), ("%", "%25"), ("=", "%3D"), (" ", "%20")]
        for a, b in pairs:
            assert escape_path_segment(a) != escape_path_segment(b)
        # distinct native strings stay distinct — never normalized into one.
        natives = ["BTC/USDT", "BTC-USDT", "btc-usdt", "BTC USDT"]
        assert len({escape_path_segment(n) for n in natives}) == len(natives)

    def test_unicode_no_normalization(self) -> None:
        nfc = "é"          # U+00E9 precomposed
        nfd = "e\u0301"    # e + combining acute (NFD-equivalent, different bytes)
        assert nfc != nfd
        assert escape_path_segment(nfc) != escape_path_segment(nfd)
        assert unescape_path_segment(escape_path_segment(nfc)) == nfc
        assert unescape_path_segment(escape_path_segment(nfd)) == nfd


class TestUnescapeRejectsNonCanonical:
    @pytest.mark.parametrize(
        "encoded",
        [
            "%",        # truncated
            "%2",       # truncated
            "%2G",      # nonhex
            "%2g",      # lowercase hex — ambiguous variant rejected
            "%2f",      # lowercase hex — ambiguous variant rejected
            "a/b",      # raw slash not canonical
            "a b",      # raw space not canonical
            "%E9",      # valid %HH but not valid UTF-8 when decoded
        ],
    )
    def test_malformed_rejected(self, encoded: str) -> None:
        with pytest.raises(ValueError):
            unescape_path_segment(encoded)


class TestProjectionObjectKey:
    def test_full_layout(self) -> None:
        assert projection_object_key(**_PROJECTION_KW) == (
            "projections/provider=kraken_futures/venue=kraken/"
            "sensor=MECHANICAL_LIQUIDATION/instrument=PI_XBTUSD/"
            "granularity=1h/year=2026/month=08/day=31/"
            "schema=liquidation_volume/part-00000-abcdef01.parquet"
        )

    def test_escapes_native_instrument(self) -> None:
        key = projection_object_key(**{**_PROJECTION_KW, "native_instrument": "BTC/USDT"})
        assert "instrument=BTC%2FUSDT" in key

    def test_schema_key_escaped_no_traversal(self) -> None:
        key = projection_object_key(**{**_PROJECTION_KW, "schema_key": "../evil"})
        assert "schema=%2E%2E%2Fevil" in key
        assert "/.." not in key

    def test_shard_padding(self) -> None:
        for shard, expected in [
            (0, "part-00000-"),
            (7, "part-00007-"),
            (12345, "part-12345-"),
            (123456, "part-123456-"),  # padding width is formatting only
        ]:
            key = projection_object_key(**{**_PROJECTION_KW, "shard_id": shard})
            assert f"/{expected}" in key

    def test_date_zero_padding(self) -> None:
        key = projection_object_key(**{**_PROJECTION_KW, "year": 2026, "month": 3, "day": 5})
        assert "/year=2026/month=03/day=05/" in key

    def test_empty_coordinates_fail_closed(self) -> None:
        for field in (
            "provider",
            "venue",
            "sensor_family",
            "native_instrument",
            "native_granularity",
            "schema_key",
        ):
            with pytest.raises(ValueError):
                projection_object_key(**{**_PROJECTION_KW, field: ""})

    def test_invalid_dates_rejected(self) -> None:
        for month, day in [(0, 1), (13, 1), (2, 30), (1, 0)]:
            with pytest.raises(ValueError):
                projection_object_key(**{**_PROJECTION_KW, "month": month, "day": day})
        with pytest.raises(ValueError):
            projection_object_key(**{**_PROJECTION_KW, "year": 0})

    def test_bad_shard_rejected(self) -> None:
        for bad in (-1, 1.5, True):
            with pytest.raises(ValueError):
                projection_object_key(**{**_PROJECTION_KW, "shard_id": bad})  # type: ignore[arg-type]

    def test_bad_prefix_length_rejected(self) -> None:
        for bad in (0, 65, True):
            with pytest.raises(ValueError):
                projection_object_key(**{**_PROJECTION_KW, "hash_prefix_length": bad})  # type: ignore[arg-type]

    def test_malformed_projection_hash_rejected(self) -> None:
        with pytest.raises(ValueError):
            projection_object_key(**{**_PROJECTION_KW, "projection_sha256": DIGEST.upper()})

    def test_deterministic(self) -> None:
        assert projection_object_key(**_PROJECTION_KW) == projection_object_key(**_PROJECTION_KW)


class TestResolveUnderRoot:
    def test_valid_key_resolves_lexically(self, tmp_path) -> None:
        result = resolve_under_root(tmp_path, "blobs/sha256/ab/cd/abc.blob")
        assert result == tmp_path / "blobs" / "sha256" / "ab" / "cd" / "abc.blob"
        assert not result.exists()  # zero filesystem mutation

    @pytest.mark.parametrize(
        "key",
        [
            "/abs/path",
            "C:/evil",
            "..",
            "../x",
            "blobs/sha256/../x",
            "blobs/./x",
            "blobs//x",
            "blobs/x/",       # trailing empty segment
        ],
    )
    def test_unsafe_keys_rejected(self, tmp_path, key: str) -> None:
        with pytest.raises(ValueError):
            resolve_under_root(tmp_path, key)

    def test_backslash_and_nul_rejected(self, tmp_path) -> None:
        with pytest.raises(ValueError):
            resolve_under_root(tmp_path, "blobs\\x")
        with pytest.raises(ValueError):
            resolve_under_root(tmp_path, "blobs/\x00x")

    def test_empty_rejected(self, tmp_path) -> None:
        with pytest.raises(ValueError):
            resolve_under_root(tmp_path, "")


class TestOSIndependentKeys:
    def test_forward_slash_separators_only(self) -> None:
        keys = [
            blob_object_key(DIGEST, StorageEncoding.NONE),
            blob_object_key(DIGEST, StorageEncoding.ZSTD),
            projection_object_key(**_PROJECTION_KW),
        ]
        for key in keys:
            assert "\\" not in key
            assert key == key.replace("\\", "/")


class TestPathAdversarial:
    """Deterministic parameterized adversarial + property-style regressions (I02 §42/§44)."""

    @pytest.mark.parametrize(
        "value",
        [
            "..",
            "../x",
            "x/../y",
            "/x",
            "\\",
            "..\\x",
            "%",
            "%2F",
            ".",
            "...",
            "\x00",
            "\x00evil",
            "PI\x00XBT",
            "a=b&c",
            "a b\tc",
            "\n",
            "\r",
            "héllo",
            "世界",
            "e\u0301",
            "💹",
            "\ufeff",
            "a" * 1000,
        ],
    )
    def test_round_trip_and_no_structure(self, value: str) -> None:
        encoded = escape_path_segment(value)
        assert unescape_path_segment(encoded) == value
        assert "/" not in encoded and "\\" not in encoded
        assert "\x00" not in encoded

    def test_encoded_output_only_canonical_alphabet(self) -> None:
        import re

        for value in ("../x", "BTC/USDT", "a=b", "héllo", "\x00", "\n"):
            encoded = escape_path_segment(value)
            assert re.fullmatch(r"(?:[A-Za-z0-9_-]|%[0-9A-F]{2})+", encoded)

    def test_escape_injective_on_native_id_pairs(self) -> None:
        natives = [
            "/", "%2F", ".", "%2E", "%", "%25", "=", "%3D", " ", "%20",
            "..", "...", "a/b", "a\\b", "a b", "ab", "a\tb", "é", "e\u0301",
            "BTC/USDT", "BTC-USDT", "btc-usdt", "BTC USDT", "%2f",
        ]
        encodings = [escape_path_segment(n) for n in natives]
        assert len(set(encodings)) == len(natives)

    def test_all_byte_values_round_trip(self) -> None:
        # Every Unicode code point 0..255 encoded as a str must round-trip.
        for code in range(256):
            char = chr(code)
            assert unescape_path_segment(escape_path_segment(char)) == char

    def test_long_native_value(self) -> None:
        value = "instrument_" + "x" * 5000 + "/with-slashes"
        encoded = escape_path_segment(value)
        assert unescape_path_segment(encoded) == value
        assert "/" not in encoded
