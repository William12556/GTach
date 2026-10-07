#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Packaging, service unit and deployment scripts.

Covers change-52653cd6 (audit-36b6ea95 G01, G02, G03, G04, G06, G08,
E05). Static checks over pyproject.toml, bin/gtach.service and the
scripts, plus unit tests for the version source and the mock touch
fallback's log level.
"""

import importlib
import importlib.metadata
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import gtach
import gtach.utils.platform as platform_module
from gtach.display.touch_interface import HyperPixelTouchInterface

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin"
EDITED_SCRIPTS = [
    "build.sh",
    "install.sh",
    "deploy.sh",
    "pull_logs.sh",
    "release.sh",
    "gtach-preflight.sh",
    "gtach-audit-checks.sh",
]


def _pyproject():
    text = (ROOT / "pyproject.toml").read_text()
    try:
        import tomllib
    except ImportError:  # Python < 3.11
        tomllib = None
    if tomllib is not None:
        return tomllib.loads(text)
    pi = re.search(r"^pi = \[(.*?)\]", text, re.S | re.M).group(1)
    deps = re.search(r"^dependencies = \[(.*?)\]", text, re.S | re.M).group(1)
    return {
        "project": {
            "dependencies": re.findall(r'"([^"]+)"', deps),
            "optional-dependencies": {"pi": re.findall(r'"([^"]+)"', pi)},
        }
    }


class TestPyproject:

    def test_pi_extra_and_dependencies(self):
        project = _pyproject()["project"]
        pi = " ".join(project["optional-dependencies"]["pi"])
        deps = " ".join(project["dependencies"])

        assert "hyperpixel2r" in pi
        assert "RPi.GPIO" in pi
        assert "gpiozero" not in pi
        assert "click" not in deps

    def test_urls_point_to_repository(self):
        text = (ROOT / "pyproject.toml").read_text()
        assert "github.com/user/" not in text
        assert "https://github.com/William12556/GTach" in text


class TestVersion:

    def test_init_has_no_literal_version(self):
        text = (ROOT / "src" / "gtach" / "__init__.py").read_text()
        # A release number such as '0.4.3'; the '0+unknown' fallback is not one.
        assert not re.search(r"__version__\s*=\s*['\"]\d+\.\d", text)

    def test_unknown_without_metadata(self, monkeypatch):
        def _missing(name):
            raise importlib.metadata.PackageNotFoundError(name)

        monkeypatch.setattr(importlib.metadata, "version", _missing)
        try:
            importlib.reload(gtach)
            assert gtach.__version__ == "0+unknown"
        finally:
            monkeypatch.undo()
            importlib.reload(gtach)

    def test_build_does_not_write_init(self):
        assert "src/gtach/__init__.py" not in (BIN / "build.sh").read_text()


class TestMockFallbackLogLevel:

    @pytest.mark.parametrize(
        "on_pi, level", [(True, logging.ERROR), (False, logging.INFO)]
    )
    def test_level(self, monkeypatch, caplog, on_pi, level):
        monkeypatch.setattr(platform_module, "is_raspberry_pi", lambda: on_pi)
        iface = object.__new__(HyperPixelTouchInterface)
        iface.logger = logging.getLogger("test.packaging.touch")

        with caplog.at_level(logging.INFO, logger="test.packaging.touch"):
            iface._start_mock_implementation()

        records = [
            r for r in caplog.records if "Using mock HyperPixel" in r.getMessage()
        ]
        assert [r.levelno for r in records] == [level]

    def test_detection_failure_falls_back_to_info(self, monkeypatch):
        def _boom():
            raise RuntimeError("no detector")

        monkeypatch.setattr(platform_module, "is_raspberry_pi", _boom)
        iface = object.__new__(HyperPixelTouchInterface)
        iface.logger = logging.getLogger("test.packaging.touch")

        assert iface._mock_fallback_log() == iface.logger.info


class TestServiceUnit:

    @pytest.mark.parametrize(
        "directive",
        [
            "TimeoutStopSec=30",
            "NoNewPrivileges=yes",
            "PrivateTmp=yes",
            "ProtectHome=yes",
            "ProtectSystem=full",
            "StartLimitBurst=5",
            "StartLimitIntervalSec=120",
            "Wants=bluetooth.service",
        ],
    )
    def test_directive_present(self, directive):
        lines = [
            line.strip() for line in (BIN / "gtach.service").read_text().splitlines()
        ]
        assert directive in lines


class TestScripts:

    @pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
    @pytest.mark.parametrize("script", EDITED_SCRIPTS)
    def test_bash_syntax(self, script):
        result = subprocess.run(
            ["bash", "-n", str(BIN / script)], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr

    def test_gen_splash_compiles(self):
        source = (BIN / "gen_splash.py").read_text()
        compile(source, "gen_splash.py", "exec")

    def test_install_uses_pi_extra(self):
        assert '"${WHEEL_PATH}[pi]"' in (BIN / "install.sh").read_text()

    def test_deploy_stops_after_all_copies(self):
        text = (BIN / "deploy.sh").read_text()
        last_scp = text.rindex("scp ")
        assert text.index("systemctl stop gtach") > last_scp
        assert "systemctl start gtach" not in text

    def test_preflight_runs_pip_check(self):
        assert '"$VENV/bin/pip" check' in (BIN / "gtach-preflight.sh").read_text()
