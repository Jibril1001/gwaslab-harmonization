"""Tests for loading configuration files from disk."""

from __future__ import annotations

import pytest

from gwaslab_harmonization import ConfigError, load_config


def test_load_config_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "does_not_exist.yaml")


def test_load_config_empty_file(tmp_path):
    config_path = tmp_path / "empty.yaml"
    config_path.write_text("", encoding="utf-8")
    with pytest.raises(ConfigError, match="empty"):
        load_config(config_path)


def test_load_config_writes_and_resolves(tmp_path, valid_config):
    data = valid_config()
    config_path = tmp_path / "config.yaml"
    import yaml

    config_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    config = load_config(config_path, base_dir=tmp_path)
    assert config.input.path.is_file()
    assert config.gwaslab_build_code == "19"
    assert config.source_path == config_path


def test_load_config_rejects_unknown_section(tmp_path, valid_config):
    import yaml

    data = valid_config()
    data["extra"] = {"nope": True}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="Unknown top-level section"):
        load_config(config_path, base_dir=tmp_path)


def test_load_config_rejects_missing_section(tmp_path, valid_config):
    import yaml

    data = valid_config()
    del data["reference"]
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ConfigError, match="Missing required section"):
        load_config(config_path, base_dir=tmp_path)


def test_bundled_config_is_valid():
    """The shipped config/harmonization.yaml must at least load and validate."""

    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    config = load_config(repo_root / "config" / "harmonization.yaml", base_dir=repo_root)
    assert config.reference.genome_build == "hg19"
    assert config.input.path.is_file()
