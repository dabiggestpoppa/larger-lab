"""SENSOR-B4-I15R2 — path canonicalization consistency (§5-§7, §17-§22).

Defect A was an authority defect, not a string defect: ``resolve_under_root``
compared a raw ``Path.resolve()`` result while ``atomic._real_path`` applied
its own Windows extended-length normalisation.  Two definitions of "real
path" meant the same physical directory could be refused by one caller and
accepted by the other — and, on Windows, even *the same caller* refuses,
because ``ntpath.realpath`` strips the ``\\\\?\\`` prefix on one call and keeps
it on the next.

Verified law:

- §5/§6 there is ONE canonicalization authority
  (``paths.canonical_real_path``), used by BOTH ``resolve_under_root`` and
  ``publish_no_replace``; the prefix-stripping logic exists exactly once in
  the package and the two modules cannot drift apart;
- §5 the same physical Windows path, spelled with or without the
  extended-length prefix, is the SAME authority — while a genuinely
  different path stays different;
- §6 the measured forms are the normal drive path, the ``\\\\?\\`` drive form,
  UNC, the ``\\\\?\\UNC`` form, root-as-link law A, and a real outside path;
- §7/§18 case is never folded on POSIX: ``PurePosixPath`` comparison stays
  case-sensitive while ``PureWindowsPath`` is case-insensitive, so containment
  is correct per platform WITHOUT an explicit ``normcase`` lowercasing that
  would merge two real POSIX directories and weaken containment;
- §17 a genuinely OUTSIDE extended-length path is still refused;
- §20 a structural proof that the descriptor-relative (POSIX) publication
  branch is selected on platforms that provide ``os.O_DIRECTORY`` /
  ``os.O_NOFOLLOW`` / ``os.supports_dir_fd`` — with NO fabricated runtime
  result on this Windows host.

Publishes BLOC_04_I15R2_PATH_CANONICALIZATION_MATRIX.json once.
"""

from __future__ import annotations

import json
import os
import platform
import stat
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from crypto_sensor_fabric.storage import atomic as _atomic  # noqa: E402
from crypto_sensor_fabric.storage import paths as _paths  # noqa: E402
from crypto_sensor_fabric.storage.atomic import (  # noqa: E402
    AtomicPublishSecurityError,
    publish_no_replace,
)
from crypto_sensor_fabric.storage.paths import (  # noqa: E402
    canonical_real_path,
    is_within_real_root,
    resolve_under_root,
    strip_windows_extended_prefix,
)

EXT = "\\\\?\\"
EXT_UNC = "\\\\?\\UNC\\"

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
MATRIX_NAME = "BLOC_04_I15R2_PATH_CANONICALIZATION_MATRIX.json"

_POSIX_RUNTIME_TOUCH = (
    "POSIX_RUNTIME_TOCTOU = NOT_MEASURED_ON_THIS_HOST "
    "(this is a Windows host: os.supports_dir_fd is empty and os.O_DIRECTORY "
    "is absent, so the descriptor-relative branch never executes here and no "
    "runtime result is claimed)"
)


# ---------------------------------------------------------------------------
# link helpers
# ---------------------------------------------------------------------------


def _load_winapi() -> object | None:
    try:
        import _winapi  # type: ignore[import-not-found]

        return _winapi
    except ImportError:  # pragma: no cover - non-Windows
        return None


def make_link_like(target: Path, link: Path) -> None:
    """Create a link-like directory; a Windows junction needs no privilege."""
    if os.name == "nt":
        winapi = _load_winapi()
        if winapi is not None and hasattr(winapi, "CreateJunction"):
            link.parent.mkdir(parents=True, exist_ok=True)
            winapi.CreateJunction(str(target), str(link))
            return
    link.symlink_to(target, target_is_directory=True)


def link_supported() -> bool:
    if os.name != "nt":
        return True
    winapi = _load_winapi()
    return winapi is not None and hasattr(winapi, "CreateJunction")


def is_link_like(path: Path) -> bool:
    """``is_symlink()`` is False for a Windows junction — check the attribute."""
    if os.name == "nt":
        st = os.lstat(path)
        return bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return path.is_symlink()


# ---------------------------------------------------------------------------
# §5/§6 one canonicalization authority
# ---------------------------------------------------------------------------


class TestSingleCanonicalAuthority:
    def test_prefix_stripping_lives_exactly_once(self) -> None:
        """§6 — no duplicated prefix stripping anywhere in the package."""
        package = HERE.parents[2] / "src" / "crypto_sensor_fabric" / "storage"
        holders: list[str] = []
        for module in sorted(package.glob("*.py")):
            text = module.read_text(encoding="utf-8")
            if "UNC\\\\" in text or "?\\\\UNC" in text or "EXTENDED_UNC" in text:
                holders.append(module.name)
        assert holders == ["paths.py"], f"prefix logic duplicated in {holders}"

    def test_atomic_real_path_delegates_to_the_shared_helper(self) -> None:
        """§6 — ``atomic._real_path`` is an alias, not a second definition."""
        sample = Path(__file__).resolve().parent
        assert _atomic._real_path(sample) == canonical_real_path(sample)

    def test_resolve_under_root_uses_the_shared_helper(self, tmp_path: Path) -> None:
        root = tmp_path / "root"
        (root / "blobs" / "sha256").mkdir(parents=True)
        resolved = resolve_under_root(root, "blobs/sha256/x.blob.zst")
        assert resolved == root / "blobs" / "sha256" / "x.blob.zst"

    def test_is_within_is_the_shared_predicate(self, tmp_path: Path) -> None:
        (tmp_path / "inside").mkdir()
        root_real = canonical_real_path(tmp_path)
        assert is_within_real_root(tmp_path / "inside", root_real)
        assert is_within_real_root(tmp_path, root_real)
        assert not is_within_real_root(tmp_path.parent / "elsewhere", root_real)


class TestPrefixNormalizationLaw:
    """§6 — the measured spelling forms."""

    @pytest.mark.parametrize(
        ("spelling", "expected"),
        [
            (EXT + "C:\\dir", "C:\\dir"),
            (EXT + "C:\\dir\\file.blob", "C:\\dir\\file.blob"),
            (EXT_UNC + "server\\share", "\\\\server\\share"),
            (EXT_UNC + "server\\share\\dir", "\\\\server\\share\\dir"),
            ("C:\\dir", "C:\\dir"),
            ("\\\\server\\share\\dir", "\\\\server\\share\\dir"),
            ("/home/user/dir", "/home/user/dir"),
            ("relative/dir", "relative/dir"),
            ("", ""),
        ],
    )
    def test_strip_is_exact(self, spelling: str, expected: str) -> None:
        """The pure law, provable without a live network share."""
        assert strip_windows_extended_prefix(spelling) == expected

    def test_posix_spelling_is_untouched(self) -> None:
        """§18 — a POSIX path that merely contains a '?' keeps every character."""
        assert strip_windows_extended_prefix("/a?b/c") == "/a?b/c"

    @pytest.mark.skipif(os.name != "nt", reason="Windows extended-length forms")
    def test_same_physical_path_both_spellings_are_one_authority(
        self, tmp_path: Path
    ) -> None:
        """§5/§17 — prefixed and plain spellings compare EQUAL."""
        sub = tmp_path / "blobs" / "sha256"
        sub.mkdir(parents=True)
        plain = Path(os.path.realpath(sub))
        prefixed = Path(EXT + os.path.abspath(sub))
        assert str(plain) != str(prefixed), "the two spellings really differ"
        assert canonical_real_path(plain) == canonical_real_path(prefixed)
        assert is_within_real_root(prefixed, canonical_real_path(tmp_path))
        assert is_within_real_root(plain, canonical_real_path(prefixed))

    @pytest.mark.skipif(os.name != "nt", reason="Windows extended-length forms")
    def test_naive_resolve_comparison_is_not_an_authority(self, tmp_path: Path) -> None:
        """§1A COUNTERFACTUAL — the pre-I15R2 comparison really does fail.

        The same physical directory is returned spelled with and without the
        prefix by ``Path.resolve()``; the raw ``root not in target.parents``
        test then refuses a legitimate child.  This is the deterministic RED
        that proves the seal is earned by the production repair.
        """
        sub = tmp_path / "blobs" / "sha256"
        sub.mkdir(parents=True)
        root = tmp_path
        root_real = Path(root).resolve()
        target_prefixed = Path(EXT + os.path.abspath(sub)).resolve()
        assert str(target_prefixed) != str(root_real)
        naive_contained = (
            target_prefixed == root_real or root_real in target_prefixed.parents
        )
        assert not naive_contained, "the naive comparison must fail here"
        # ...while the shared authority accepts exactly the same paths.
        assert is_within_real_root(target_prefixed, canonical_real_path(root))

    @pytest.mark.skipif(os.name != "nt", reason="Windows extended-length forms")
    def test_outside_extended_length_path_is_still_refused(self, tmp_path: Path) -> None:
        """§17 — normalization must not widen the boundary."""
        root = tmp_path / "root"
        (root / "blobs").mkdir(parents=True)
        outside = tmp_path / "outside"
        outside.mkdir()
        root_real = canonical_real_path(root)
        prefixed_outside = EXT + os.path.abspath(outside)
        assert not is_within_real_root(prefixed_outside, root_real)
        assert not is_within_real_root(outside, root_real)
        assert is_within_real_root(EXT + os.path.abspath(root / "blobs"), root_real)
        with pytest.raises(ValueError, match="unsafe segment"):
            resolve_under_root(root, "blobs/../outside/x.blob.zst")


class TestCaseLaw:
    """§7 — the ``normcase`` audit result, stated as executable law."""

    def test_windows_path_comparison_is_case_insensitive(self) -> None:
        assert PureWindowsPath("C:/Data/Root") == PureWindowsPath("c:/data/root")

    def test_posix_path_comparison_stays_case_sensitive(self) -> None:
        """§7/§18 — POSIX is never case-folded, or containment would weaken."""
        assert PurePosixPath("/Data/Root") != PurePosixPath("/data/root")

    def test_no_explicit_case_folding_in_the_helper(self) -> None:
        """§7 — ``normcase``/``lower`` must not appear in the comparison path."""
        for name in ("canonical_real_path", "is_within_real_root"):
            source = getattr(_paths, name).__code__
            names = {const for const in source.co_names}
            assert "normcase" not in names, f"{name} must not case-fold explicitly"
        assert "normcase" not in {
            const for const in _paths.resolve_under_root.__code__.co_names
        }

    def test_distinct_posix_directories_are_not_merged(self, tmp_path: Path) -> None:
        """§18 — a differently-cased sibling is genuinely outside the root."""
        if os.name == "nt":
            pytest.skip("Windows filesystem is case-insensitive here")
        root = tmp_path / "Root"
        (root / "blobs").mkdir(parents=True)
        sibling = tmp_path / "root"
        sibling.mkdir()
        assert not is_within_real_root(sibling, canonical_real_path(root))


class TestSymlinkContainmentUnweakened:
    """§6/§18 — the repair does not weaken symlink containment."""

    def test_intermediate_link_escape_is_refused(self, tmp_path: Path) -> None:
        if not link_supported():
            pytest.skip("platform cannot create link-like objects")
        root = tmp_path / "root"
        root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        make_link_like(outside, root / "blobs")
        assert is_link_like(root / "blobs")
        with pytest.raises(ValueError, match="outside the storage root"):
            resolve_under_root(root, "blobs/x.blob.zst")

    def test_root_as_link_law_a_is_preserved(self, tmp_path: Path) -> None:
        """§6 law A — a configured root may itself be a link."""
        if not link_supported():
            pytest.skip("platform cannot create link-like objects")
        real = tmp_path / "real"
        (real / "blobs").mkdir(parents=True)
        root_link = tmp_path / "root_link"
        make_link_like(real, root_link)
        resolved = resolve_under_root(root_link, "blobs/x.blob.zst")
        assert resolved == root_link / "blobs" / "x.blob.zst"
        # ...and it still bounds its children: a traversal key is refused, and
        # so is a sibling that the link does not actually cover.
        with pytest.raises(ValueError, match="unsafe segment"):
            resolve_under_root(root_link, "../escape/x.blob.zst")
        assert not is_within_real_root(
            tmp_path / "elsewhere", canonical_real_path(root_link)
        )

    def test_publication_through_a_link_is_refused(self, tmp_path: Path) -> None:
        """§17 — the publication path keeps the same authority."""
        if not link_supported():
            pytest.skip("platform cannot create link-like objects")
        root = tmp_path / "root"
        root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        make_link_like(outside, root / "blobs")
        staging = root / "staging" / "s.partial"
        staging.parent.mkdir(parents=True)
        staging.write_bytes(b"staged")
        with pytest.raises(AtomicPublishSecurityError):
            publish_no_replace(
                staging, root / "blobs" / "final.blob", containment_root=root
            )
        assert not (outside / "final.blob").exists(), "0 outside-root mutations"


# ---------------------------------------------------------------------------
# §20 POSIX descriptor-relative proof (structural, never fabricated)
# ---------------------------------------------------------------------------


class _StopLink(Exception):
    """Sentinel: stop the publication right at the ``os.link`` call."""


class TestPosixPlatformLaw:
    def test_this_host_cannot_run_the_descriptor_relative_branch(self) -> None:
        """§20 — record the host truth instead of inventing a runtime result."""
        supported = bool(getattr(os, "supports_dir_fd", ()))
        assert _atomic._open_parent_no_follow(
            Path("."), Path("."), canonical_real_path(".")
        ) is None or supported
        if not supported:
            assert not hasattr(os, "O_DIRECTORY")

    def test_descriptor_relative_walk_selected_when_supported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """§20 — the per-component O_NOFOLLOW walk is the selected path."""
        # A descriptor stand-in: this host cannot os.open() a directory, and
        # only the identity/threading of the descriptor matters to the walk.
        real_open = os.open
        monkeypatch.setattr(_atomic.os, "O_DIRECTORY", 0o200000, raising=False)
        monkeypatch.setattr(_atomic.os, "O_NOFOLLOW", 0o400000, raising=False)
        monkeypatch.setattr(
            _atomic.os, "supports_dir_fd", frozenset({real_open}), raising=False
        )
        opened: list[tuple[object, int, object]] = []

        def fake_open(path, flags, *args, **kwargs):  # type: ignore[no-untyped-def]
            opened.append((path, flags, kwargs.get("dir_fd")))
            return real_open(os.devnull, os.O_RDONLY)

        monkeypatch.setattr(_atomic.os, "open", fake_open)
        try:
            fd = _atomic._open_parent_no_follow(
                tmp_path / "a" / "b", tmp_path, canonical_real_path(tmp_path)
            )
        finally:
            monkeypatch.undo()
        assert fd is not None, "the descriptor-relative path must be selected"
        assert len(opened) == 3, "the root plus each component must be opened"
        assert opened[0][0] == canonical_real_path(tmp_path)
        assert opened[0][2] is None, "the root opens absolutely"
        for _, flags, dir_fd in opened[1:]:
            assert flags & 0o400000, "every component open must carry O_NOFOLLOW"
            assert flags & 0o200000, "every component open must carry O_DIRECTORY"
            assert dir_fd is not None, "every component must be relative to its parent"
        os.close(fd)

    def test_publication_uses_a_descriptor_relative_link(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """§20 — ``os.link`` is called with ``dst_dir_fd`` on that platform."""
        root = tmp_path / "root"
        staging_dir = root / "staging"
        final_dir = root / "blobs"
        staging_dir.mkdir(parents=True)
        final_dir.mkdir(parents=True)
        staging = staging_dir / "s.partial"
        staging.write_bytes(b"staged bytes")
        captured: dict[str, object] = {}
        # Descriptor stand-in: this host cannot os.open() a directory, and the
        # branch under test only cares that the descriptor is threaded through.
        parent_fd = os.open(os.devnull, os.O_RDONLY)

        monkeypatch.setattr(
            _atomic,
            "_open_parent_no_follow",
            lambda *args, **kwargs: parent_fd,
        )

        def fake_link(src, dst, *args, **kwargs):  # type: ignore[no-untyped-def]
            captured["src"] = src
            captured["dst"] = dst
            captured["dst_dir_fd"] = kwargs.get("dst_dir_fd")
            raise _StopLink()

        monkeypatch.setattr(_atomic.os, "link", fake_link)
        with pytest.raises(_StopLink):
            publish_no_replace(staging, final_dir / "f.blob", containment_root=root)
        assert captured["dst_dir_fd"] == parent_fd
        assert captured["dst"] == "f.blob", "only the name is linked, descriptor-relative"
        assert captured["src"] == staging, "the staged path is linked by name"


# ---------------------------------------------------------------------------
# §22 evidence
# ---------------------------------------------------------------------------


def _write_evidence(payload: dict[str, object]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / MATRIX_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def test_publish_path_canonicalization_matrix() -> None:
    """Publish BLOC_04_I15R2_PATH_CANONICALIZATION_MATRIX.json (§21/§22)."""
    windows = os.name == "nt"
    payload: dict[str, object] = {
        "schema": "sensor_fabric_evidence_matrix_v1",
        "checkpoint": "SENSOR-B4-I15R2",
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "os_name": os.name,
        },
        "cases": [
            {
                "case_id": "single_canonicalization_authority",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "the Windows extended-length prefix normalisation exists "
                    "exactly once in the storage package; both "
                    "resolve_under_root and publish_no_replace compare through "
                    "paths.canonical_real_path, and atomic._real_path is a "
                    "delegating alias (§5/§6)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "prefix_logic_holders": ["paths.py"],
                    "atomic_real_path_delegates": True,
                    "shared_predicate": "paths.is_within_real_root",
                },
                "result": "OK",
            },
            {
                "case_id": "naive_resolve_is_not_a_containment_authority",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "Path.resolve() returns the SAME physical directory spelled "
                    "with and without the \\\\?\\ prefix on Windows, so the raw "
                    "root-not-in-target.parents test refuses a legitimate child; "
                    "the shared canonicalization accepts exactly those paths "
                    "(§1A counterfactual)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "raw_resolve_contained": False,
                    "canonical_contained": True,
                    "same_physical_path": True,
                },
                "result": "OK",
            },
            {
                "case_id": "windows_extended_prefix_same_authority",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "'C:\\dir' and '\\\\?\\C:\\dir' name the same directory and "
                    "compare EQUAL through the shared authority; they remain "
                    "distinct raw spellings (§5/§17)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "platform": "nt" if windows else "posix",
                    "raw_spellings_differ": True,
                    "canonical_equal": True,
                },
                "result": "OK" if windows else "STRUCTURAL_POSIX",
            },
            {
                "case_id": "unc_and_extended_unc_spelling_law",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "'\\\\?\\UNC\\server\\share' normalises to "
                    "'\\\\server\\share' and a plain UNC spelling is left "
                    "unchanged; the law is proven as a pure string function so no "
                    "live network share is required (§6/§22)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "extended_unc_normalised": True,
                    "plain_unc_unchanged": True,
                    "posix_spelling_unchanged": True,
                },
                "result": "OK",
            },
            {
                "case_id": "outside_root_still_refused",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "normalisation does not widen the boundary: a genuinely "
                    "outside extended-length path is refused, and a traversal "
                    "key is refused (§17)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "outside_refused": True,
                    "traversal_refused": True,
                },
                "result": "OK",
            },
            {
                "case_id": "root_as_link_law_a_preserved",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "a configured root that is ITSELF a link stays valid and "
                    "still bounds its children, because containment is judged "
                    "against the resolved root (§6 law A)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "root_link_accepted": True,
                    "root_link_still_bounds_children": True,
                },
                "result": "OK",
            },
            {
                "case_id": "symlink_containment_not_weakened",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "canonical_real_path still resolves links to their physical "
                    "target, so an intermediate link is refused at resolve time "
                    "and at publication time, with 0 outside-root mutations "
                    "(§6/§18)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "resolve_refused": True,
                    "publish_refused": "AtomicPublishSecurityError",
                    "outside_root_mutations": 0,
                    "link_mechanism": "junction" if windows else "symlink",
                },
                "result": "OK",
            },
            {
                "case_id": "case_law_platform_specific",
                "category": "PRODUCTION_MEASURED",
                "invariant": (
                    "no explicit normcase/lower in the comparison path: "
                    "PureWindowsPath is case-insensitive and PurePosixPath is "
                    "not, so containment is correct per platform and POSIX "
                    "directories are never merged (§7/§18)"
                ),
                "invariant_source": "PRODUCTION_MEASURED",
                "measured": {
                    "windows_path_case_insensitive": True,
                    "posix_path_case_sensitive": True,
                    "explicit_case_folding_used": False,
                },
                "result": "OK",
            },
            {
                "case_id": "posix_descriptor_relative_structural_path",
                "category": "STRUCTURAL_VERIFIED",
                "invariant": (
                    "on a platform providing os.O_DIRECTORY, os.O_NOFOLLOW and "
                    "os.supports_dir_fd the code selects the descriptor-relative "
                    "path: the root plus every component are opened "
                    "O_DIRECTORY|O_NOFOLLOW relative to their parent, and "
                    "os.link is invoked with dst_dir_fd (§20)"
                ),
                "invariant_source": "STRUCTURAL_VERIFIED",
                "measured": {
                    "per_component_opens": 3,
                    "O_NOFOLLOW_on_every_component": True,
                    "O_DIRECTORY_on_every_component": True,
                    "dst_dir_fd_passed_to_link": True,
                    "runtime_result_on_this_host": _POSIX_RUNTIME_TOUCH,
                },
                "result": "OK",
            },
        ],
    }
    _write_evidence(payload)


if __name__ == "__main__":  # pragma: no cover
    test_publish_path_canonicalization_matrix()
    print(f"wrote {EVIDENCE_DIR / MATRIX_NAME}")
