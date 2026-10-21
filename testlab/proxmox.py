"""Minimal Proxmox snapshot helper for lab-only tests (spec 007 AC6; spec 009 grows it).

Uses the ai-deploy-test@pve token from ~/.config/ai-deploy/proxmox.env and only
touches the VMID it's given, which must be a test slot (AGENTS.md) - checked
here before any API call, as well as by the token's ACL. Never imported by
onboard/ (AGENTS.md). Never prints the token.
"""

import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV_FILE = Path.home() / ".config" / "ai-deploy" / "proxmox.env"
TASK_TIMEOUT = 300
SLOTS = (range(9101, 9111), range(9201, 9211))


def _env():
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _call(verb, path, params=None):
    env = _env()
    url = f"https://{env['PROXMOX_HOST']}:8006/api2/json/nodes/{env['PROXMOX_NODE']}{path}"
    data = None
    if params and verb == "DELETE":
        url += "?" + urllib.parse.urlencode(params)
    elif params:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=verb)  # noqa: S310 - fixed https URL
    req.add_header(
        "Authorization", f"PVEAPIToken={env['PROXMOX_TOKEN_ID']}={env['PROXMOX_TOKEN_SECRET']}"
    )
    # The PVE certificate is self-signed; pinning it is spec 009's job.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:  # noqa: S310
            return json.load(r).get("data")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Proxmox {verb} {path}: HTTP {e.code} {e.reason}") from None


def _slot(vmid):
    """The VMID as an int, or ValueError if it isn't one of the test slots."""
    try:
        n = int(vmid)
    except (TypeError, ValueError):
        n = None
    if n is None or not any(n in r for r in SLOTS):
        raise ValueError(f"VMID {vmid!r} is not a test slot (9101-9110, 9201-9210)")
    return n


def _wait(upid):
    deadline = time.monotonic() + TASK_TIMEOUT
    while time.monotonic() < deadline:
        status = _call("GET", f"/tasks/{urllib.parse.quote(upid, safe='')}/status")
        if status.get("status") == "stopped":
            if status.get("exitstatus") != "OK":
                raise RuntimeError(f"Proxmox task {upid} failed: {status.get('exitstatus')}")
            return
        time.sleep(2)
    raise RuntimeError(f"Proxmox task {upid} didn't finish within {TASK_TIMEOUT}s")


def snapshot(vmid, name):
    vmid = _slot(vmid)
    _wait(_call("POST", f"/qemu/{vmid}/snapshot", {"snapname": name}))


def rollback(vmid, name):
    vmid = _slot(vmid)
    _wait(_call("POST", f"/qemu/{vmid}/snapshot/{name}/rollback"))


def start(vmid):
    vmid = _slot(vmid)
    status = _call("GET", f"/qemu/{vmid}/status/current")
    if status.get("status") != "running":
        _wait(_call("POST", f"/qemu/{vmid}/status/start"))


def delete_snapshot(vmid, name):
    vmid = _slot(vmid)
    _wait(_call("DELETE", f"/qemu/{vmid}/snapshot/{name}"))


def ipv4(vmid, timeout=180):
    """The VM's first non-loopback IPv4 address, from the QEMU guest agent."""
    vmid = _slot(vmid)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            reply = _call("GET", f"/qemu/{vmid}/agent/network-get-interfaces")
        except RuntimeError:
            reply = None  # agent not up yet
        for iface in (reply or {}).get("result", []):
            for addr in iface.get("ip-addresses", []):
                ip = addr["ip-address"]
                if addr["ip-address-type"] == "ipv4" and not ip.startswith(("127.", "169.254.")):
                    return ip
        time.sleep(5)
    raise RuntimeError(f"VM {vmid} reported no IPv4 address within {timeout}s")
