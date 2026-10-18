"""Tests for reporting helpers."""

from __future__ import annotations

import json

from gwaslab_harmonization import (
    format_config_summary,
    get_version_info,
    run_harmonization,
    validate_config,
    write_run_manifest,
)


def test_format_config_summary(valid_config):
    config = validate_config(valid_config())
    summary = format_config_summary(config)
    assert "Harmonization configuration" in summary
    assert "genome build" in summary
    assert "hg19 (GWASLab code 19)" in summary


def test_get_version_info_reports_platform():
    info = get_version_info()
    assert "python" in info
    assert "gwaslab" in info


def test_write_run_manifest(valid_config, fake_gwaslab, tmp_path):
    config = validate_config(valid_config())
    result = run_harmonization(config, gl=fake_gwaslab, save=False)

    manifest_path = write_run_manifest(
        result, config, manifest_path=tmp_path / "run_manifest.json", gl=fake_gwaslab
    )

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["input"]["n_variants"] == 15
    assert payload["output"]["saved"] is False
    assert payload["gwaslab_sumstats_kwargs"]["build"] == "19"
    assert payload["gwaslab_harmonize_kwargs"]["threads"] == 1
    assert payload["versions"]["gwaslab"] == "4.2.3-fake"
