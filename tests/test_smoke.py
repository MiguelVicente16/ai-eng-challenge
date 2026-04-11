"""Smoke test to verify the project is set up correctly."""


def test_imports():
    import src.config
    assert src.config is not None
