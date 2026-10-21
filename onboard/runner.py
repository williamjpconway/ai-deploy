"""The only place onboarding touches the network or runs a process.

Unit tests replace a Runner with a stub that has the same two methods.
"""

from dataclasses import dataclass


@dataclass
class Result:
    returncode: int
    stdout: str
    stderr: str
