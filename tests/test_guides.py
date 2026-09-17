import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def test_guide_timing_navigation_and_local_artifact_links():
    root = Path(__file__).resolve().parents[1]
    enrollment = (root / "src" / "parse_834.py").exists()
    modules = ["00-start", "01-landing", "02-ingestion", "03-products", "04-report", "05-validate", "06-wrap-up"]
    durations = [10, 20, 30, 30, 25, 10, 5] if enrollment else [10, 25, 25, 25, 30, 10, 5]
    for module, minutes in zip(modules, durations, strict=True):
        path = root / "lab-guide" / f"{module}.md"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# ")
        assert f"**Duration:** {minutes} minutes" in text
        assert "[Guide](README.md)" in text
        assert "Answer" in text
    assert sum(durations) == 130
    for path in [root / "README.md", *(root / "lab-guide").glob("*.md"),
                 *(root / "docs").glob("*.md"),
                 *(root / "instructor").glob("*.md")]:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            parsed = urlsplit(target)
            if not parsed.scheme and parsed.path:
                assert (path.parent / unquote(parsed.path)).exists(), f"Broken local link: {path.name}: {target}"


def test_instructor_handoff_and_requirement_mapping():
    root = Path(__file__).resolve().parents[1]
    enrollment = (root / "src" / "parse_834.py").exists()
    prefix, count = ("EDI", 7) if enrollment else ("DA", 8)
    mapping = (root / "docs" / "requirements-traceability.md").read_text(encoding="utf-8")
    for number in range(1, count + 1):
        assert f"| {prefix}-{number:02d} |" in mapping
    runbook = (root / "instructor" / "README.md").read_text(encoding="utf-8")
    assert "no cross-run lease" in runbook
    assert "non-owner" in runbook
    assert "your tenant" in runbook
    assert (root / "docs" / "data-dictionary.md").exists()
