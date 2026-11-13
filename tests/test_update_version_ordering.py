"""Version ordering of the update check.

Covers issue-c41037ea and change-c41037ea (audit-bce0d69a H01): the
update check reads PEP 440 pre-release versions and orders them below
their final release, so a release candidate can be updated from a staged
wheel and can itself be offered as an update.
"""

import logging
import zipfile
from pathlib import Path
from typing import Optional

import pytest

from gtach.utils import updater


def _key(version: str):
    key = updater._parse_version_str(version)
    assert key is not None, version
    return key


def _stage(directory: Path, version: str) -> str:
    """Write a valid zip named as the wheel of the given version."""
    name = f"gtach-{version}-py3-none-any.whl"
    with zipfile.ZipFile(directory / name, "w") as wheel:
        wheel.writestr("gtach/__init__.py", "")
    return name


@pytest.fixture
def updates_dir(tmp_path, monkeypatch):
    """A temporary updates directory; the installed version is set per test."""
    monkeypatch.setattr(updater, "UPDATES_DIR", str(tmp_path))
    return tmp_path


def _install(monkeypatch, version: Optional[str]) -> None:
    monkeypatch.setattr(
        updater,
        "get_installed_version",
        lambda: None if version is None else updater._parse_version_str(version),
    )


class TestOrderKey:
    def test_pre_releases_order_below_the_final_release(self):
        ordered = [
            "0.5.0",
            "1.0.0a1",
            "1.0.0b2",
            "1.0.0rc1",
            "1.0.0rc2",
            "1.0.0",
            "1.0.1",
            "1.1.0",
        ]
        keys = [_key(version) for version in ordered]
        assert keys == sorted(keys)
        assert len(set(keys)) == len(keys)

    def test_short_release_equals_padded_release(self):
        assert _key("1.0") == _key("1.0.0")
        assert _key("1") == _key("1.0.0")

    def test_pre_release_of_a_short_release(self):
        assert _key("1.0rc1") == _key("1.0.0rc1")
        assert _key("1.0rc1") < _key("1.0")

    def test_four_component_release(self):
        assert _key("1.0.0") < _key("1.0.0.1") < _key("1.0.1")

    def test_surrounding_whitespace_is_ignored(self):
        assert _key(" 1.0.0rc1\n") == _key("1.0.0rc1")

    @pytest.mark.parametrize(
        "text",
        ["", "abc", "1.0.0.dev1", "1.0.0+local", "1.0.0-rc.1", "1..0", "1.0.0rc", None],
    )
    def test_unsupported_forms_give_none(self, text):
        assert updater._parse_version_str(text) is None

    def test_wheel_filename_of_a_release_candidate(self):
        assert updater.parse_wheel_version("gtach-1.0.0rc1-py3-none-any.whl") == _key(
            "1.0.0rc1"
        )

    def test_filename_without_a_version(self):
        assert updater.parse_wheel_version("gtach.whl") is None


class TestFindAvailableUpdate:
    def test_final_release_is_offered_to_a_release_candidate(
        self, updates_dir, monkeypatch
    ):
        _install(monkeypatch, "1.0.0rc1")
        name = _stage(updates_dir, "1.0.0")
        assert updater.find_available_update() == (name, "1.0.0")

    def test_release_candidate_is_offered_to_an_earlier_release(
        self, updates_dir, monkeypatch
    ):
        _install(monkeypatch, "0.5.0")
        name = _stage(updates_dir, "1.0.0rc1")
        assert updater.find_available_update() == (name, "1.0.0rc1")

    def test_older_and_pre_release_wheels_are_not_offered_to_the_final_release(
        self, updates_dir, monkeypatch
    ):
        _install(monkeypatch, "1.0.0")
        _stage(updates_dir, "1.0.0rc1")
        _stage(updates_dir, "0.5.0")
        _stage(updates_dir, "1.0.0")
        assert updater.find_available_update() is None

    def test_newest_of_several_wheels_is_offered(self, updates_dir, monkeypatch):
        _install(monkeypatch, "1.0.0rc1")
        _stage(updates_dir, "1.0.0rc2")
        name = _stage(updates_dir, "1.0.0")
        assert updater.find_available_update() == (name, "1.0.0")

    def test_unrecognised_installed_version_is_logged(
        self, updates_dir, monkeypatch, caplog
    ):
        _install(monkeypatch, None)
        _stage(updates_dir, "1.0.0")
        with caplog.at_level(logging.WARNING, logger=updater.logger.name):
            assert updater.find_available_update() is None
        assert any(
            record.levelno == logging.WARNING
            and "Installed version not recognised" in record.getMessage()
            for record in caplog.records
        )

    def test_wheel_with_unrecognised_version_is_skipped(
        self, updates_dir, monkeypatch, caplog
    ):
        _install(monkeypatch, "0.5.0")
        _stage(updates_dir, "1.0.0.dev1")
        with caplog.at_level(logging.DEBUG, logger=updater.logger.name):
            assert updater.find_available_update() is None
        assert any("unrecognised version" in r.getMessage() for r in caplog.records)

    def test_invalid_zip_is_skipped(self, updates_dir, monkeypatch):
        _install(monkeypatch, "0.5.0")
        (updates_dir / "gtach-1.0.0-py3-none-any.whl").write_bytes(b"not a zip")
        assert updater.find_available_update() is None


def test_installed_version_reads_package_metadata(monkeypatch):
    import importlib.metadata

    monkeypatch.setattr(importlib.metadata, "version", lambda name: "1.0.0rc1")
    assert updater.get_installed_version() == _key("1.0.0rc1")
