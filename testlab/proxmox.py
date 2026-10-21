"""Minimal Proxmox snapshot helper for lab-only tests (spec 007 AC6, grown by spec 009)."""


def snapshot(vmid, name):
    raise NotImplementedError


def rollback(vmid, name):
    raise NotImplementedError


def start(vmid):
    raise NotImplementedError


def delete_snapshot(vmid, name):
    raise NotImplementedError
