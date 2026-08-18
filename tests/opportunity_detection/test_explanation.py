import sys

from cross_silo_opportunity_engine.opportunity_detection.explanation import generate_rationale


def test_generate_rationale_returns_none_when_anthropic_not_installed(monkeypatch):
    # Setting sys.modules["anthropic"] = None makes `import anthropic` raise ImportError,
    # simulating an environment where the optional llm extra was never installed.
    monkeypatch.setitem(sys.modules, "anthropic", None)
    assert generate_rationale({"entity_name": "Acme"}, ["high_value_deal"]) is None


def test_generate_rationale_returns_none_on_api_failure(monkeypatch):
    import anthropic

    class _FailingMessages:
        def create(self, **kwargs):
            raise RuntimeError("simulated API failure")

    class _FailingClient:
        def __init__(self):
            self.messages = _FailingMessages()

    monkeypatch.setattr(anthropic, "Anthropic", lambda: _FailingClient())

    assert generate_rationale({"entity_name": "Acme"}, ["high_value_deal"]) is None


def test_generate_rationale_returns_grounded_text_on_success(monkeypatch):
    import anthropic

    class _TextBlock:
        type = "text"
        text = "  Acme qualifies because of a large, urgent deal.  "

    class _FakeResponse:
        content = [_TextBlock()]

    class _FakeMessages:
        def create(self, **kwargs):
            return _FakeResponse()

    class _FakeClient:
        def __init__(self):
            self.messages = _FakeMessages()

    monkeypatch.setattr(anthropic, "Anthropic", lambda: _FakeClient())

    result = generate_rationale({"entity_name": "Acme"}, ["high_value_deal"])
    assert result == "Acme qualifies because of a large, urgent deal."
