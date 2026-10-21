"""Minimal Proxmox snapshot helper for lab-only tests (spec 007 AC6; spec 009 grows it).

Uses the ai-deploy-test@pve token from ~/.config/ai-deploy/proxmox.env and only
touches the VMID it's given - Proxmox itself refuses anything outside the test
slots. Never imported by onboard/ (AGENTS.md). Never prints the token.
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
    req = urllib.request.Request(url, data=data, method=verb)
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
    _wait(_call("POST", f"/qemu/{vmid}/snapshot", {"snapname": name}))


def rollback(vmid, name):
    _wait(_call("POST", f"/qemu/{vmid}/snapshot/{name}/rollback"))


def start(vmid):
    status = _call("GET", f"/qemu/{vmid}/status/current")
    if status.get("status") != "running":
        _wait(_call("POST", f"/qemu/{vmid}/status/start"))


def delete_snapshot(vmid, name):
    _wait(_call("DELETE", f"/qemu/{vmid}/snapshot/{name}"))
