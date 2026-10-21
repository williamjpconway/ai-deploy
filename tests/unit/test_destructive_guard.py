"""Run 3 fix T14: a destructive fixture only changes a target that is the lab
slot (AI_DEPLOY_TEST_LAB_VMID, matched by IP) or that the operator named with
--confirmed-target; anything else is skipped before any change."""

import pytest
from helpers import require_slot_or_confirmed

from testlab import proxmox


class Config:
    def __init__(self, confirmed=()):
        self.confirmed = list(confirmed)

    def getoption(self, name):
        assert name == "--confirmed-target"
        return self.confirmed


@pytest.fixture
def slot_at(monkeypatch):
    def at(ip):
        monkeypatch.setenv("AI_DEPLOY_TEST_LAB_VMID", "9201")
        monkeypatch.setattr(proxmox, "ipv4", lambda vmid, timeout=180: ip)

    return at


def test_non_slot_unconfirmed_target_is_skipped(monkeypatch):
    monkeypatch.delenv("AI_DEPLOY_TEST_LAB_VMID", raising=False)
    with pytest.raises(pytest.skip.Exception, match="--confirmed-target"):
        require_slot_or_confirmed(Config(), "192.168.3.1")


def test_confirmation_for_another_ip_does_not_count(monkeypatch):
    monkeypatch.delenv("AI_DEPLOY_TEST_LAB_VMID", raising=False)
    with pytest.raises(pytest.skip.Exception):
        require_slot_or_confirmed(Config(["192.168.3.9"]), "192.168.3.1")


def test_confirmed_target_is_allowed(monkeypatch):
    monkeypatch.delenv("AI_DEPLOY_TEST_LAB_VMID", raising=False)
    require_slot_or_confirmed(Config(["192.168.3.1"]), "192.168.3.1")


def test_lab_slot_at_the_target_ip_is_allowed(slot_at):
    slot_at("192.168.0.84")
    require_slot_or_confirmed(Config(), "192.168.0.84")


def test_lab_slot_elsewhere_does_not_cover_the_target(slot_at):
    slot_at("192.168.0.84")
    with pytest.raises(pytest.skip.Exception, match="slot 9201 is at 192.168.0.84"):
        require_slot_or_confirmed(Config(), "192.168.0.99")
