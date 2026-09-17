"""Capture an authenticated report without storing tokens or browser state."""

import argparse
import csv
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

import requests
from playwright.sync_api import TimeoutError as BrowserTimeout, sync_playwright

from fabric import FabricClient


REPORT_VALUES = {
    "catalog": [6, 4, 1, 8],
    "spend": [8725, 8450, 275, 0.8231],
    "reconciliation": [11305, 480, 2100, 436.25],
    "health": [13, 7, 6, 26],
    "exceptions": [16, 10, 0.769, 0],
    "review": [13, 10, 16, 0],
}


def card_values(page, allow_blank=False):
    exports = page.evaluate("""async () => {
        const active = (await report.getPages()).find(item => item.isActive);
        const values = {};
        for (const visual of (await active.getVisuals()).filter(item => item.type === 'card')) {
            values[visual.name] = (await visual.exportData(0, 10)).data;
        }
        return values;
    }""")
    values = {}
    for name, content in exports.items():
        rows = list(csv.reader(io.StringIO(content.lstrip("\ufeff"))))
        if allow_blank and len(rows) in (1, 2) and len(rows[0]) == 1 and (len(rows) == 1 or not rows[1]):
            values[name] = None
            continue
        if len(rows) != 2 or len(rows[1]) != 1:
            raise AssertionError(f"Card {name} did not export one value")
        text = rows[1][0].strip()
        value = float(text.replace(",", "").replace("$", "").rstrip("%"))
        values[name] = value / 100 if text.endswith("%") else value
    return values


def activate_page(page, name):
    previous_render = page.evaluate("window.renderCount")
    changed = page.evaluate("""async name => {
        const target = (await report.getPages()).find(item => item.name === name);
        if (target.isActive) return false;
        await target.setActive();
        return true;
    }""", name)
    if changed:
        page.wait_for_function("previous => window.renderCount > previous", arg=previous_render, timeout=180000)


def verify(workspace, report_id, output, channel=None):
    UUID(workspace)
    UUID(report_id)
    client = FabricClient()
    token = client.credential.get_token("https://analysis.windows.net/powerbi/api/.default").token
    response = requests.get(
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace}/reports/{report_id}",
        headers={"Authorization": f"Bearer {token}"}, timeout=60, allow_redirects=False)
    response.raise_for_status()
    report_info = response.json()
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=channel, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1, locale="en-US")
        page = context.new_page()
        page_errors, console_errors, http_failures = [], [], []
        page.on("pageerror", lambda error: page_errors.append(str(error).replace(token, "[redacted]")[:2000]))
        page.on("console", lambda message: console_errors.append(message.text.replace(token, "[redacted]")[:2000])
            if message.type == "error" else None)

        def capture_response(response):
            if response.status >= 400:
                address = urlsplit(response.url)
                http_failures.append({"host": address.hostname, "path": address.path, "status": response.status})

        page.on("response", capture_response)
        page.set_content('<!doctype html><html lang="en-US"><head><title>Fabric report validation</title></head>'
                         '<body style="margin:0"><div id="report" style="width:1440px;height:900px"></div></body></html>')
        page.add_script_tag(url="https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js")
        page.evaluate("""config => {
            window.reportErrors = [];
            window.renderCount = 0;
            window.reportLoaded = false;
            window.report = powerbi.embed(document.getElementById('report'), {
                type: 'report', id: config.id, embedUrl: config.embedUrl,
                accessToken: config.token, tokenType: 0,
                permissions: 0,
                settings: {localeSettings: {language: 'en-us', formatLocale: 'en-us'},
                    panes: {filters: {visible: false}, pageNavigation: {visible: true}}}
            });
            report.on('loaded', () => window.reportLoaded = true);
            report.on('rendered', () => window.renderCount++);
            report.on('error', event => window.reportErrors.push(event.detail.message || 'Unspecified report error'));
        }""", {"id": report_id, "embedUrl": report_info["embedUrl"], "token": token})
        page.wait_for_function("window.reportLoaded || window.reportErrors.length", timeout=180000)
        errors = page.evaluate("window.reportErrors")
        if errors:
            raise RuntimeError(f"Report load failed: {errors}")
        loaded_pages = page.evaluate("async () => (await report.getPages()).map(item => ({name:item.name, title:item.displayName, visibility:item.visibility}))")
        try:
            page.wait_for_function("window.renderCount > 0 || window.reportErrors.length", timeout=60000)
        except BrowserTimeout:
            page.screenshot(path=str(output / "render-timeout.png"), full_page=True)
            diagnostics = {"errors": page.evaluate("window.reportErrors"), "pages": loaded_pages,
                           "page_errors": page_errors, "console_errors": console_errors,
                           "http_failures": http_failures, "frames": []}
            for frame in page.frames:
                diagnostics["frames"].append(frame.locator("body").inner_text(timeout=10000)[:5000])
            (output / "render-timeout.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
            raise
        if page.evaluate("window.reportErrors.length"):
            raise RuntimeError(f"Report render failed: {page.evaluate('window.reportErrors')}")
        pages = page.evaluate("async () => (await report.getPages()).filter(item => item.visibility === 0).map(item => ({name:item.name, title:item.displayName}))")
        if len(pages) != 3:
            raise AssertionError(f"Expected three visible pages, received {len(pages)}")
        evidence = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "workspace_id": workspace,
                    "report_id": report_id, "dataset_id": report_info["datasetId"],
                    "access_context": "authenticated_instructor_owner", "sdk_version": "2.23.1", "pages": []}
        for report_page in pages:
            activate_page(page, report_page["name"])
            visuals = page.evaluate("""async name => {
                const active = (await report.getPages()).find(item => item.name === name);
                return (await active.getVisuals()).map(item => ({name:item.name, type:item.type, title:item.title}));
            }""", report_page["name"])
            if len(visuals) < 3:
                raise AssertionError("Report page has too few visuals")
            values = card_values(page)
            expected = {f"metric{index}": value for index, value in enumerate(REPORT_VALUES[report_page["name"]])}
            if values.keys() != expected.keys() or any(
                    not math.isclose(values[name], value, rel_tol=0, abs_tol=0.000001)
                    for name, value in expected.items()):
                raise AssertionError(f"Unexpected rendered values on {report_page['name']}: {values}")
            page.screenshot(path=str(output / f"{report_page['name']}.png"), full_page=True)
            evidence["pages"].append({**report_page, "visuals": visuals, "card_values": values})
        first_page = pages[0]["name"]
        activate_page(page, first_page)
        baseline = card_values(page)
        target, selected = ({"table": "Catalog", "column": "document_id"}, "D001") if first_page == "catalog" else (
            {"table": "Members", "column": "member_ordinal"}, 5)
        selected_filter = {"$schema": "http://powerbi.com/product/schema#basic", "target": target,
                           "operator": "In", "values": [selected], "filterType": 1}
        try:
            previous_render = page.evaluate("window.renderCount")
            page.evaluate("async selected => report.setFilters([selected])", selected_filter)
            page.wait_for_function("previous => window.renderCount > previous", arg=previous_render, timeout=180000)
            filtered = card_values(page, allow_blank=True)
            if filtered["metric0"] != 1:
                raise AssertionError(f"Single-record filter failed: {filtered}")
            page.screenshot(path=str(output / "filtered.png"), full_page=True)
        finally:
            previous_render = page.evaluate("window.renderCount")
            page.evaluate("async () => report.removeFilters()")
            page.wait_for_function("previous => window.renderCount > previous", arg=previous_render, timeout=180000)
        restored = card_values(page)
        if restored != baseline:
            raise AssertionError("Clearing the report filter did not restore the original values")
        evidence["filter_check"] = {"status": "passed", "target": target, "selected": selected,
                                    "baseline": baseline, "filtered": filtered, "restored": restored}
        evidence["errors"] = page.evaluate("window.reportErrors")
        evidence["page_errors"] = page_errors
        evidence["console_errors"] = console_errors
        evidence["http_failures"] = http_failures
        evidence["status"] = "passed" if not evidence["errors"] and not page_errors else "failed"
        browser.close()
    (output / "report-check.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    if evidence["status"] != "passed":
        raise AssertionError(f"Report emitted errors: {evidence['errors'] + page_errors}")
    return {"report_id": report_id, "pages": [item["name"] for item in pages],
            "rendered_values": "passed", "filter_check": "passed", "errors": evidence["errors"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--channel", choices=["msedge", "chrome"])
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments.workspace, arguments.report, arguments.output, arguments.channel), indent=2))