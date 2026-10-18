"""Tests for configuration validation rules (no file I/O beyond the input)."""

from __future__ import annotations

import pytest

from gwaslab_harmonization import ConfigError, validate_config


def test_defaults_applied(valid_config):
    config = validate_config(valid_config())
    assert config.input.format == "gwaslab"
    assert config.input.other_columns == ("NOTE",)
    assert config.harmonization.threads == 1
    assert config.harmonization.maf_threshold == 0.40
    assert config.output.filename == "harmonized.tsv"


@pytest.mark.parametrize(
    "build,expected", [("hg19", "19"), ("GRCh37", "19"), ("38", "38"), ("hg38", "38")]
)
def test_genome_build_aliases(valid_config, build, expected):
    data = valid_config()
    data["reference"] = {"genome_build": build}
    assert validate_config(data).gwaslab_build_code == expected


def test_unsupported_genome_build(valid_config):
    data = valid_config()
    data["reference"] = {"genome_build": "hg17"}
    with pytest.raises(ConfigError, match="Unsupported reference.genome_build"):
        validate_config(data)


def test_missing_input_file(valid_config, tmp_path):
    data = valid_config()
    data["input"]["path"] = str(tmp_path / "missing.tsv")
    with pytest.raises(ConfigError, match="Input summary-statistics file not found"):
        validate_config(data)


def test_output_must_not_overwrite_input(valid_config, input_file):
    data = valid_config()
    data["output"]["directory"] = str(input_file.parent)
    data["output"]["filename"] = input_file.name
    with pytest.raises(ConfigError, match="refusing to overwrite input"):
        validate_config(data)


def test_output_filename_rejects_separators(valid_config):
    data = valid_config()
    data["output"]["filename"] = "nested/harmonized.tsv"
    with pytest.raises(ConfigError, match="must not contain a directory separator"):
        validate_config(data)


def test_inference_vcf_requires_af_field(valid_config, input_file):
    vcf = input_file.parent / "ref.vcf.gz"
    vcf.write_text("", encoding="utf-8")
    data = valid_config()
    data["reference"] = {"genome_build": "hg19", "inference_vcf_path": str(vcf)}
    with pytest.raises(ConfigError, match="allele_frequency_field.*required"):
        validate_config(data)


def test_af_field_without_vcf_is_rejected(valid_config):
    data = valid_config()
    data["reference"] = {"genome_build": "hg19", "allele_frequency_field": "AF"}
    with pytest.raises(ConfigError, match="inference_vcf_path.*not"):
        validate_config(data)


def test_configured_reference_must_exist(valid_config):
    data = valid_config()
    data["reference"] = {"genome_build": "hg19", "fasta_path": "nope.fa"}
    with pytest.raises(ConfigError, match="reference.fasta_path does not exist"):
        validate_config(data)


def test_warning_when_no_reference_resources(valid_config):
    config = validate_config(valid_config())
    assert any("standardization/basic checks only" in w for w in config.warnings)


def test_no_warning_when_fasta_present(valid_config, input_file):
    fasta = input_file.parent / "ref.fa"
    fasta.write_text(">chr1\nA\n", encoding="utf-8")
    data = valid_config()
    data["reference"] = {"genome_build": "hg19", "fasta_path": str(fasta)}
    config = validate_config(data)
    assert config.warnings == ()


@pytest.mark.parametrize("bad", [0.0, 0.6, -0.1])
def test_maf_threshold_range(valid_config, bad):
    data = valid_config()
    data["harmonization"]["maf_threshold"] = bad
    with pytest.raises(ConfigError, match="maf_threshold"):
        validate_config(data)


def test_threads_must_be_positive_int(valid_config):
    data = valid_config()
    data["harmonization"]["threads"] = 0
    with pytest.raises(ConfigError, match="threads"):
        validate_config(data)


def test_bool_fields_are_strict(valid_config):
    data = valid_config()
    data["harmonization"]["basic_check"] = "yes"
    with pytest.raises(ConfigError, match="basic_check"):
        validate_config(data)


def test_other_columns_must_be_list_of_strings(valid_config):
    data = valid_config()
    data["input"]["other_columns"] = [1, 2]
    with pytest.raises(ConfigError, match="other_columns"):
        validate_config(data)
