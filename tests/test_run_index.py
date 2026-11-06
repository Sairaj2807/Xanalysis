from reporting.run_index import latest_run, list_runs


def test_exact_kind_matching_does_not_confuse_ablation_with_primary(tmp_path):
    for n in ["20261105T141541Z_primary", "20261105T143130Z_ablation_primary", "20261105T143517Z_all_posts",
              "20261105T150000Z_primary_fintwitbert-sentiment", "not_a_run"]:
        (tmp_path / n).mkdir()
    assert latest_run("primary", tmp_path).name == "20261105T141541Z_primary"           # ablation sorts later but must not match
    assert latest_run("ablation_primary", tmp_path).name == "20261105T143130Z_ablation_primary"
    assert latest_run("primary_fintwitbert-sentiment", tmp_path).name.endswith("fintwitbert-sentiment")
    assert latest_run("nowcast", tmp_path) is None and len(list_runs("all_posts", tmp_path)) == 1
