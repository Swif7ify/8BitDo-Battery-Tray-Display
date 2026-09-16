from __future__ import annotations

import uuid

from eightbitdo_battery_tray.single_instance import SingleInstance


def test_single_instance_nominal_lifecycle() -> None:
    unique_name = f"Local\\TestSingleInstance_{uuid.uuid4().hex}"

    with SingleInstance(name=unique_name) as first:
        assert first.already_running is False

        # Attempt to acquire same mutex concurrently
        with SingleInstance(name=unique_name) as second:
            assert second.already_running is True

    # After first closes, a new instance should successfully acquire ownership
    with SingleInstance(name=unique_name) as third:
        assert third.already_running is False
