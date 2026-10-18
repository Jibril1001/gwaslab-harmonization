"""Tests for the pipeline argument mapping and control flow using a fake GWASLab."""

from __future__ import annotations

import pytest

from gwaslab_harmonization import (
    build_harmonize_kwargs,
    build_sumstats_kwargs,
    run_harmonization,
    validate_config,
)


def test_build_sumstats_kwargs(valid_config):
    config = validate_config(valid_config())
    kwargs = build_sumstats_kwargs(config)
    assert kwargs["fmt"] == "gwaslab"
    assert kwargs["build"] == "19"
    assert kwargs["other"] == ["NOTE"]


def test_build_harmonize_kwargs_no_reference(valid_config):
    config = validate_config(valid_config())
    kwargs = build_harmonize_kwargs(config)
    assert kwargs["threads"] == 1
    assert kwargs["basic_check"] is True
    assert "ref_seq" not in kwargs
    assert "ref_infer" not in kwargs


def test_build_harmonize_kwargs_with_references(valid_config, input_file):
    fasta = input_file.parent / "ref.fa"
    fasta.write_text(">chr1\nA\n", encoding="utf-8")
    vcf = input_file.parent / "ref.vcf.gz"
    vcf.write_text("", encoding="utf-8")

    data = valid_config()
    data["reference"] = {
        "genome_build": "hg19",
        "fasta_path": str(fasta),
        "inference_vcf_path": str(vcf),
        "allele_frequency_field": "AF",
    }
    config = validate_config(data)
    kwargs = build_harmonize_kwargs(config)

    assert kwargs["ref_seq"] == str(fasta)
    assert kwargs["ref_infer"] == str(vcf)
    assert kwargs["ref_alt_freq"] == "AF"


def test_run_harmonization_end_to_end(valid_config, fake_gwaslab):
    config = validate_config(valid_config())
    result = run_harmonization(config, gl=fake_gwaslab)

    instance = fake_gwaslab.last
    assert instance.init_kwargs["fmt"] == "gwaslab"
    assert instance.init_kwargs["build"] == "19"
    assert len(instance.harmonize_calls) == 1
    assert instance.harmonize_calls[0]["threads"] == 1

    assert result.n_variants_in == 15
    assert result.n_variants_out == 14
    assert result.variant_delta == -1
    assert result.saved is True
    assert result.output_path is not None and result.output_path.is_file()
    assert instance.to_format_calls[0][1]["build"] == "19"


def test_run_harmonization_no_save(valid_config, fake_gwaslab):
    config = validate_config(valid_config())
    result = run_harmonization(config, gl=fake_gwaslab, save=False)

    assert result.saved is False
    assert result.output_path is None
    assert fake_gwaslab.last.to_format_calls == []


def test_run_harmonization_remove_shrinks_output(valid_config, fake_gwaslab):
    data = valid_config()
    data["harmonization"]["remove"] = True
    config = validate_config(data)
    result = run_harmonization(config, gl=fake_gwaslab, save=False)
    assert result.n_variants_out == 13


def test_run_harmonization_without_gwaslab_raises(valid_config, monkeypatch):
    import gwaslab_harmonization.pipeline as pipeline

    def _raise():
        raise ImportError("GWASLab is required to run harmonization but is not installed.")

    monkeypatch.setattr(pipeline, "_import_gwaslab", _raise)
    config = validate_config(valid_config())
    with pytest.raises(ImportError, match="GWASLab is required"):
        run_harmonization(config)
