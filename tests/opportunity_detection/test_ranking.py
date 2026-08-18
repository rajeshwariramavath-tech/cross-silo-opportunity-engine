from cross_silo_opportunity_engine.opportunity_detection.ranking import rank_opportunities


def test_rank_opportunities_sorts_descending_by_composite_score():
    matches = [
        {"id": "a", "composite_score": 3},
        {"id": "b", "composite_score": 6},
        {"id": "c", "composite_score": 1},
    ]
    ranked = rank_opportunities(matches)
    assert [m["id"] for m in ranked] == ["b", "a", "c"]


def test_rank_opportunities_empty_list():
    assert rank_opportunities([]) == []
