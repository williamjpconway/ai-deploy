"""Run 1 fix T11: the lab helper itself refuses VMIDs outside the test slots
(AGENTS.md: 9101-9110, 9201-9210), not just the token's ACL."""

import pytest

from testlab import proxmox


def no_network(*args, **kwargs):
    raise AssertionError("Proxmox API called for an out-of-range VMID")


@pytest.mark.parametrize("vmid", [9000, 9001, 9100, 9111, 9200, 9211, 100, "9201; x"])
@pytest.mark.parametrize(
    "call",
    [
        lambda v: proxmox.snapshot(v, "s"),
        lambda v: proxmox.rollback(v, "s"),
        lambda v: proxmox.start(v),
        lambda v: proxmox.delete_snapshot(v, "s"),
        lambda v: proxmox.ipv4(v, timeout=0),
    ],
)
def test_vmid_outside_the_slots_is_refused_before_the_api(monkeypatch, call, vmid):
    monkeypatch.setattr(proxmox, "_call", no_network)
    with pytest.raises(ValueError, match="test slot"):
        call(vmid)


@pytest.mark.parametrize("vmid", [9101, 9110, 9201, 9210, "9201"])
def test_vmid_inside_the_slots_reaches_the_api(monkeypatch, vmid):
    seen = []
    monkeypatch.setattr(
        proxmox,
        "_call",
        lambda verb, path, params=None: seen.append(path) or {"status": "running"},
    )
    proxmox.start(vmid)
    assert seen and seen[0] == f"/qemu/{int(vmid)}/status/current"
