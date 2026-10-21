import pytest

import onboard.cli


@pytest.fixture(autouse=True)
def good_key(tmp_path, monkeypatch):
    """Unit runs get a private, 0600 key file instead of the real Key B."""
    key = tmp_path / "key_b"
    key.write_text("not a real key - the runner is stubbed\n")
    key.chmod(0o600)
    monkeypatch.setattr(onboard.cli, "DEFAULT_KEY", key)
    return key
