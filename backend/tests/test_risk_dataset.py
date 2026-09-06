from collections import Counter

from ml.generate_risk_dataset import build


def test_risk_dataset_v2_has_runtime_aligned_features():
    rows = build()
    assert len(rows) == 3000
    assert Counter(row["label"] for row in rows)["SAFE"] == 900
    assert {row["feature_schema"] for row in rows} == {"xlmr-risk-v2-json"}
    for row in rows:
        assert isinstance(row["current_state_structured"], dict)
        assert row["proposed_action_structured"]["tool"]


def test_template_groups_never_cross_splits():
    locations = {}
    for row in build():
        locations.setdefault(row["template_group"], set()).add(row["split"])
    assert all(len(splits) == 1 for splits in locations.values())
