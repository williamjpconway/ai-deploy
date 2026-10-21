"""The only place onboarding touches the network or runs a process.

Unit tests replace a Runner with a stub that has the same two methods.
"""

import socket
import subprocess
from dataclasses import dataclass


@dataclass
class Result:
    returncode: int
    stdout: str
    stderr: str


class Runner:
    def tcp_connect(self, host, port, timeout):
        """Open and close a TCP connection. Raises OSError (incl. timeout) on failure."""
        with socket.create_connection((host, port), timeout=timeout):
            pass

    def run(self, argv, timeout, env=None):
        """Run argv (never through a shell). A timeout comes back as returncode 124."""
        try:
            proc = subprocess.run(
                argv, capture_output=True, text=True, timeout=timeout, env=env
            )
        except subprocess.TimeoutExpired:
            return Result(124, "", f"timed out after {timeout}s")
        return Result(proc.returncode, proc.stdout, proc.stderr)
