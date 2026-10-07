#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""The single configuration store under GTACH_HOME.

Covers change-5fbff586 (audit-36b6ea95 E01, E02, E04, E08, G07, X04).
GTACH_HOME/config.yaml, flat schema, is the only configuration file and
ConfigStore its only owner; --validate-config can fail; DisplayManager
does no configuration file I/O of its own.

Every test works under tmp_path; nothing is written to /opt/gtach or
the repository.
"""

import logging
import sys
import types

import pytest
import yaml

import gtach.main  # noqa: F401  — ensures the module is in sys.modules
from gtach.display.manager import DisplayManager
from gtach.display.models import DAY_PALETTE, NIGHT_PALETTE, DisplayMode
from gtach.utils.config import AppConfig, ConfigStore
from gtach.utils.home import DEFAULT_GTACH_HOME, gtach_home

# gtach/__init__.py re-exports the main FUNCTION under the name 'main'
# (issue-c1d4b8e6).
gtach_main = sys.modules["gtach.main"]

DEVICE_FILE = {
    "mode": "RADIAL",
    "palette": "day",
    "engine_profile": "abarth_595_turismo",
    "fps_limit": 30,
    "touch_long_press": 1.0,
    "rpm_warning": 6500,
    "rpm_danger": 7000,
}


def _write(path, data):
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


class TestGtachHome:

    def test_unset(self, monkeypatch):
        monkeypatch.delenv("GTACH_HOME", raising=False)
        assert gtach_home() == DEFAULT_GTACH_HOME

    def test_empty(self, monkeypatch):
        monkeypatch.setenv("GTACH_HOME", "")
        assert gtach_home() == DEFAULT_GTACH_HOME

    def test_set(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GTACH_HOME", str(tmp_path))
        assert gtach_home() == tmp_path

    def test_store_default_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("GTACH_HOME", str(tmp_path))
        assert ConfigStore().path == tmp_path / "config.yaml"


class TestLoad:

    def test_missing_file_gives_defaults_and_writes_nothing(self, tmp_path):
        path = tmp_path / "config.yaml"

        assert ConfigStore(path).load() == AppConfig()
        assert not path.exists()

    def test_device_file(self, tmp_path):
        config = ConfigStore(_write(tmp_path / "config.yaml", DEVICE_FILE)).load()

        assert config.engine_profile == "abarth_595_turismo"
        assert config.fps_limit == 30
        assert config.mode == "RADIAL"

    def test_digital_maps_to_radial(self, tmp_path):
        path = _write(tmp_path / "config.yaml", {"mode": "DIGITAL"})
        assert ConfigStore(path).load().mode == "RADIAL"

    def test_invalid_value_uses_default_with_warning(self, tmp_path, caplog):
        path = _write(tmp_path / "config.yaml", {"fps_limit": "abc"})

        with caplog.at_level(logging.WARNING):
            config = ConfigStore(path).load()

        assert config.fps_limit == 30
        assert any("fps_limit" in r.getMessage() for r in caplog.records)

    def test_invalid_yaml_gives_defaults(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("mode: [unclosed\n", encoding="utf-8")
        assert ConfigStore(path).load() == AppConfig()

    def test_list_gives_defaults(self, tmp_path):
        path = _write(tmp_path / "config.yaml", ["a", "b"])
        assert ConfigStore(path).load() == AppConfig()


class TestSave:

    def test_round_trip_keeps_unknown_key(self, tmp_path):
        path = _write(tmp_path / "config.yaml", dict(DEVICE_FILE, foo=1))
        store = ConfigStore(path)
        config = store.load()
        config.palette = "night"

        assert store.save(config) is True
        assert ConfigStore(path).load() == config
        assert yaml.safe_load(path.read_text())["foo"] == 1

    def test_only_unknown_keys_preserved(self, tmp_path):
        path = _write(tmp_path / "config.yaml", {"foo": 1, "bar": "x"})
        store = ConfigStore(path)

        assert store.save(store.load()) is True
        data = yaml.safe_load(path.read_text())
        assert data["foo"] == 1 and data["bar"] == "x"

    def test_creates_missing_directory(self, tmp_path):
        path = tmp_path / "new" / "dir" / "config.yaml"

        assert ConfigStore(path).save(AppConfig()) is True
        assert path.exists()
        assert list(path.parent.iterdir()) == [path]


class TestValidate:

    def test_valid_file(self, tmp_path):
        assert (
            ConfigStore(_write(tmp_path / "config.yaml", DEVICE_FILE)).validate() == []
        )

    def test_missing_file(self, tmp_path):
        assert ConfigStore(tmp_path / "config.yaml").validate() == []

    def test_digital_is_accepted(self, tmp_path):
        path = _write(tmp_path / "config.yaml", dict(DEVICE_FILE, mode="DIGITAL"))
        assert ConfigStore(path).validate() == []

    @pytest.mark.parametrize(
        "key, value",
        [
            ("foo", 1),
            ("fps_limit", "abc"),
            ("mode", "GAUGE"),
            ("palette", "dusk"),
            ("engine_profile", "no_such_profile"),
            ("fps_limit", 0),
            ("fps_limit", 61),
            ("touch_long_press", 0.05),
            ("touch_long_press", 6.0),
        ],
    )
    def test_each_invalid_case(self, tmp_path, key, value):
        path = _write(tmp_path / "config.yaml", dict(DEVICE_FILE, **{key: value}))

        errors = ConfigStore(path).validate()

        assert len(errors) == 1
        assert key in errors[0]

    def test_not_a_mapping(self, tmp_path):
        path = _write(tmp_path / "config.yaml", ["a"])
        assert len(ConfigStore(path).validate()) == 1


@pytest.fixture
def logs(tmp_path, monkeypatch):
    """Redirect every log path and restore the root logger afterwards."""
    for name, file in (
        ("_START_LOG", "start.log"),
        ("_DEBUG_LOG", "debug.log"),
        ("_ERROR_LOG", "error.log"),
    ):
        monkeypatch.setattr(gtach_main, name, str(tmp_path / file))
    for name in ("_start_handler", "_debug_handler", "_error_handler"):
        monkeypatch.setattr(gtach_main, name, None)
    root = logging.getLogger()
    before = list(root.handlers)
    level = root.level
    yield
    for handler in list(root.handlers):
        if handler not in before:
            root.removeHandler(handler)
            try:
                handler.close()
            except Exception:
                pass
    root.setLevel(level)


class TestValidateConfigCli:

    def test_invalid_file_exits_1(self, tmp_path, monkeypatch, capsys, logs):
        path = _write(tmp_path / "config.yaml", dict(DEVICE_FILE, fps_limit=0))
        monkeypatch.setattr(
            sys, "argv", ["gtach", "--validate-config", "--config", str(path)]
        )

        assert gtach_main.main() == 1
        assert "fps_limit" in capsys.readouterr().out

    def test_valid_file_exits_0(self, tmp_path, monkeypatch, capsys, logs):
        path = _write(tmp_path / "config.yaml", DEVICE_FILE)
        monkeypatch.setattr(
            sys, "argv", ["gtach", "--validate-config", "--config", str(path)]
        )

        assert gtach_main.main() == 0
        assert "Config valid" in capsys.readouterr().out


class TestDisplayManagerUsesStore:

    def _host(self, store):
        return types.SimpleNamespace(
            _config_store=store, logger=logging.getLogger("test.config_store")
        )

    def test_palette_and_mode_round_trip(self, tmp_path):
        path = tmp_path / "config.yaml"
        store = ConfigStore(path)
        host = self._host(store)

        DisplayManager._load_config(host)
        assert not path.exists()  # defaults are not written on load
        assert host._palette is DAY_PALETTE
        assert host._post_splash_mode == DisplayMode.RADIAL

        host._palette = NIGHT_PALETTE
        DisplayManager._save_config(host)

        reloaded = self._host(ConfigStore(path))
        DisplayManager._load_config(reloaded)
        assert reloaded._palette is NIGHT_PALETTE
        assert reloaded._post_splash_mode == DisplayMode.RADIAL
        assert reloaded.config.fps_limit == 30

    def test_save_goes_through_the_store(self):
        saved = []
        store = types.SimpleNamespace(save=saved.append)
        host = self._host(store)
        host.config = types.SimpleNamespace(
            mode=DisplayMode.SPLASH,
            engine_profile="abarth_595_turismo",
            fps_limit=30,
            touch_long_press=1.0,
            rpm_warning=6500,
            rpm_danger=7000,
        )
        host._post_splash_mode = DisplayMode.RADIAL
        host._palette = NIGHT_PALETTE

        DisplayManager._save_config(host)

        assert saved == [AppConfig(palette="night")]
