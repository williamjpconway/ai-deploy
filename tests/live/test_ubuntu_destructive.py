"""Spec 007 ACs that change the Ubuntu target.

AC3: password auth switched back on via an sshd drop-in, then removed - the
     restore uses sudo, which stays working throughout.
AC6: sudo broken for real - which also breaks any sudo-based restore - so it
     only runs against a spec 009 lab slot (AI_DEPLOY_TEST_LAB_VMID) and is
     restored by Proxmox snapshot rollback. Optional: skipped without the lab.

Both need --allow-destructive. Against a 009 slot no operator confirmation is
needed (AGENTS.md sandbox exception); against anything else it is.
"""

import os
import time

import pytest
from conftest import ubuntu_ssh
from helpers import check_tag, snapshot

DROPIN = "/etc/ssh/sshd_config.d/00-a-test-password.conf"
RESTART = "sudo systemctl restart ssh.socket ssh.service"


@pytest.fixture
def password_auth_on(ubuntu_ip, tmp_path):
    kh = tmp_path / "admin_known_hosts"
    on = ubuntu_ssh(
        ubuntu_ip,
        kh,
        f"echo 'PasswordAuthentication yes' | sudo tee {DROPIN} >/dev/null && {RESTART}",
    )
    assert on.returncode == 0, on
    try:
        yield ubuntu_ip
    finally:
        off = ubuntu_ssh(ubuntu_ip, kh, f"sudo rm -f {DROPIN} && {RESTART}")
        check = ubuntu_ssh(ubuntu_ip, kh, "sudo sshd -T | grep -i '^passwordauthentication'")
        print(f"after restore: {check.stdout.strip()}")
        assert off.returncode == 0, off
        assert check.stdout.strip().lower() == "passwordauthentication no", check


@pytest.mark.live_ubuntu
@pytest.mark.destructive
def test_ac3_password_auth_enabled_fails_password_auth(ubuntu_cli, password_auth_on, inventory_dir):
    proc = ubuntu_cli("--name", "ubuntu-test", "--ip", password_auth_on)
    assert proc.returncode != 0
    assert check_tag(proc.output) == "password-auth"
    assert snapshot(inventory_dir) == {}


@pytest.fixture
def sudo_broken_on_lab_slot(ubuntu_ip, tmp_path):
    from testlab import proxmox

    vmid = int(os.environ["AI_DEPLOY_TEST_LAB_VMID"])
    snap = f"pre-ac6-{int(time.time())}"
    kh = tmp_path / "admin_known_hosts"
    # The rollback restores the slot, so sudo may only be broken on the slot
    # itself - refuse before changing anything if the target IP is elsewhere.
    slot_ip = proxmox.ipv4(vmid)
    assert slot_ip == ubuntu_ip, (
        f"slot {vmid} is at {slot_ip}, not the target {ubuntu_ip} - nothing changed"
    )
    proxmox.snapshot(vmid, snap)
    try:
        # Both grants: initialize-ssh-onboarding.sh's and cloud-init's own.
        broke = ubuntu_ssh(
            ubuntu_ip,
            kh,
            "sudo mv /etc/sudoers.d/90-masterchief /etc/sudoers.d/90-cloud-init-users /tmp/",
        )
        assert broke.returncode == 0, broke
        check = ubuntu_ssh(ubuntu_ip, kh, "sudo -n true 2>/dev/null && echo still-has-sudo")
        assert "still-has-sudo" not in check.stdout, "sudo still passwordless - test is wrong"
        yield ubuntu_ip
    finally:
        proxmox.rollback(vmid, snap)
        proxmox.start(vmid)
        # Plain DHCP: the slot may come back on a different address.
        ip = proxmox.ipv4(vmid)
        print(f"slot {vmid} back at {ip}" + ("" if ip == ubuntu_ip else " (IP changed)"))
        ok = None
        for _ in range(30):
            ok = ubuntu_ssh(ip, kh, "sudo -n true && echo sudo-ok")
            if "sudo-ok" in ok.stdout:
                break
            time.sleep(5)
        proxmox.delete_snapshot(vmid, snap)
        assert ok is not None and "sudo-ok" in ok.stdout, ok


@pytest.mark.live_ubuntu
@pytest.mark.destructive
@pytest.mark.lab
def test_ac6_no_passwordless_sudo_fails_identity(
    ubuntu_cli, sudo_broken_on_lab_slot, inventory_dir
):
    proc = ubuntu_cli("--name", "ubuntu-test", "--ip", sudo_broken_on_lab_slot)
    assert proc.returncode != 0
    assert check_tag(proc.output) == "identity"
    assert "NOPASSWD" in proc.output
    assert snapshot(inventory_dir) == {}
