from cross_silo_opportunity_engine.opportunity_detection.rules import Rule, evaluate_rules


def test_evaluate_rules_returns_only_fired_rule_names_in_order():
    rules = [
        Rule("always_true", lambda m: True),
        Rule("always_false", lambda m: False),
        Rule("checks_value", lambda m: m["value"] > 10),
    ]
    assert evaluate_rules({"value": 20}, rules) == ["always_true", "checks_value"]
    assert evaluate_rules({"value": 5}, rules) == ["always_true"]


def test_evaluate_rules_empty_rule_list():
    assert evaluate_rules({}, []) == []
