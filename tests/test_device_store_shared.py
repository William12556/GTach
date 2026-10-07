#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""One shared, locked DeviceStore under GTACH_HOME.

Covers change-453f0a80 (audit-36b6ea95 A09, A10). Independent unlocked
DeviceStore instances at a working-directory-relative path could lose
each other's writes; the shared instance lives at
gtach_home()/config/devices.yaml, locks every public method and fsyncs
before the rename.

GTACH_HOME points at tmp_path in every test; conftest resets the shared
instance after each test.
"""

import os
import threading

import pytest
import yaml

import gtach.comm.device_store as device_store_module
from gtach.comm.device_store import (
    DeviceStore,
    get_device_store,
    reset_device_store,
)
from gtach.comm.models import BluetoothDevice

JOIN_TIMEOUT = 10.0
PER_THREAD = 50


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv('GTACH_HOME', str(tmp_path))
    reset_device_store()
    return tmp_path


def _device(prefix, index):
    return BluetoothDevice(name=f'{prefix}{index}',
                           mac_address=f'{prefix}:00:00:00:00:{index:02X}',
                           device_type='ELM327')


class TestSharedInstance:

    def test_same_object(self):
        assert get_device_store() is get_device_store()

    def test_default_path_under_gtach_home(self, home):
        assert get_device_store().config_path == str(home / 'config' / 'devices.yaml')

    def test_visible_from_another_call_site(self):
        get_device_store().save_device(_device('AA', 1))

        primary = get_device_store().get_primary_device()

        assert primary is not None
        assert primary.mac_address == 'AA:00:00:00:00:01'

    def test_reset_gives_new_object(self):
        first = get_device_store()
        reset_device_store()

        assert get_device_store() is not first


class TestConcurrency:

    def test_two_threads_saving_secondaries(self, home):
        store = get_device_store()
        errors = []

        def worker(prefix):
            try:
                for i in range(PER_THREAD):
                    assert store.save_device(_device(prefix, i), is_primary=False)
            except Exception as e:  # pragma: no cover - failure path
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(p,), daemon=True) for p in ('AA', 'BB')]
        for t in threads:
            t.start()
        for t in threads:
            t.join(JOIN_TIMEOUT)

        assert all(not t.is_alive() for t in threads)
        assert errors == []
        with open(home / 'config' / 'devices.yaml') as f:
            data = yaml.safe_load(f)
        assert len(data['paired_devices']['secondary']) == 2 * PER_THREAD
        assert len(store.get_all_devices()) == 2 * PER_THREAD

    def test_every_public_method_takes_the_lock(self):
        """Each public method blocks while another thread holds the lock."""
        store = get_device_store()
        calls = [
            lambda: store.save_device(_device('AA', 1)),
            store.get_primary_device,
            store.get_all_devices,
            lambda: store.remove_device('AA:00:00:00:00:01'),
            lambda: store.get_device_by_mac('AA:00:00:00:00:01'),
        ]
        for call in calls:
            done = threading.Event()
            store._lock.acquire()
            try:
                t = threading.Thread(target=lambda: (call(), done.set()), daemon=True)
                t.start()
                assert not done.wait(0.1)
            finally:
                store._lock.release()
            assert done.wait(JOIN_TIMEOUT)


class TestDurableSave:

    def test_fsync_before_replace(self, monkeypatch):
        store = get_device_store()
        order = []
        real_fsync, real_replace = os.fsync, os.replace
        monkeypatch.setattr(device_store_module.os, 'fsync',
                            lambda fd: (order.append('fsync'), real_fsync(fd)))
        monkeypatch.setattr(device_store_module.os, 'replace',
                            lambda a, b: (order.append('replace'), real_replace(a, b)))

        assert store._save_config() is True
        assert order == ['fsync', 'replace']


class TestPatchedClass:

    def test_accessor_constructs_through_module_name(self, monkeypatch):
        sentinel = object()
        monkeypatch.setattr(device_store_module, 'DeviceStore', lambda: sentinel)

        assert get_device_store() is sentinel
