from solution.build_model import MEASURES, TABLES
from solution.build_report import build


def test_report_fields_exist_and_visuals_fit_each_page():
    parts = build("11111111-1111-4111-8111-111111111111")
    assert parts["definition.pbir"]["version"] == "4.0"
    assert parts["definition/version.json"]["version"] == "2.0.0"
    assert len(parts["definition/pages/pages.json"]["pageOrder"]) == 3
    assert isinstance(parts["definition/report.json"]["themeCollection"]["customTheme"]["reportVersionAtImport"], str)
    themes = parts["definition/report.json"]["themeCollection"]
    assert themes["baseTheme"]["name"] == "CY24SU06"
    assert themes["baseTheme"]["reportVersionAtImport"] == themes["customTheme"]["reportVersionAtImport"] == "5.55"
    for path, content in parts.items():
        if not path.endswith("visual.json"):
            continue
        if content["visual"]["visualType"] == "card":
            assert content["visual"]["objects"]["categoryLabels"][0]["properties"]["show"]["expr"]["Literal"]["Value"] == "false"
            assert content["visual"]["objects"]["labels"][0]["properties"]["fontSize"]["expr"]["Literal"]["Value"] == "32"
        position = content["position"]
        assert 0 <= position["x"] < position["x"] + position["width"] <= 1280
        assert 0 <= position["y"] < position["y"] + position["height"] <= 720
        for role in content["visual"].get("query", {}).get("queryState", {}).values():
            for projection in role["projections"]:
                kind, field = next(iter(projection["field"].items()))
                source = field["Expression"]["SourceRef"]["Entity"]
                names = {measure[0] for measure in MEASURES.get(source, [])} if kind == "Measure" else TABLES[source][1]
                assert field["Property"] in names


def test_report_rebinds_only_to_explicit_model():
    model = "22222222-2222-4222-8222-222222222222"
    reference = build(model)["definition.pbir"]["datasetReference"]
    assert reference == {"byConnection": {"connectionString": f"semanticmodelid={model}"}}