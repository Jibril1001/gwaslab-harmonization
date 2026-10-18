"""Shared pytest fixtures.

The GWASLab dependency (and its native ``pysam``/htslib stack and multi-GB
reference data) is not required to test this workflow. Instead we inject a fake
``gwaslab`` module that records how it was called, which is exactly what these
tests assert on: configuration handling and argument mapping.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the src/ layout importable when running from a source checkout.
_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


TOY_TSV = (
    "SNPID\tCHR\tPOS\tEA\tNEA\tEAF\tBETA\tSE\tP\tN\n1:2:A:T\t1\t2\tA\tT\t0.5\t0.1\t0.2\t0.3\t1000\n"
)


class FakeSumstats:
    """Minimal stand-in for ``gwaslab.Sumstats``."""

    def __init__(self, path: str, **kwargs):
        self.path = path
        self.init_kwargs = kwargs
        # Length only; ``harmonize`` may shrink it (simulating variant removal).
        self.data = list(range(15))
        self.harmonize_calls: list[dict] = []
        self.to_format_calls: list[tuple[str, dict]] = []

    def harmonize(self, **kwargs):
        self.harmonize_calls.append(kwargs)
        if kwargs.get("remove"):
            self.data = self.data[:13]
        else:
            self.data = self.data[:14]

    def to_format(self, path: str, **kwargs):
        self.to_format_calls.append((path, kwargs))
        Path(path).write_text("dummy output\n", encoding="utf-8")


class FakeGWASLab:
    """Minimal stand-in for the ``gwaslab`` module object."""

    __version__ = "4.2.3-fake"

    def __init__(self):
        self.instances: list[FakeSumstats] = []

    def Sumstats(self, path, **kwargs):
        instance = FakeSumstats(path, **kwargs)
        self.instances.append(instance)
        return instance

    @property
    def last(self) -> FakeSumstats:
        return self.instances[-1]


@pytest.fixture
def fake_gwaslab() -> FakeGWASLab:
    return FakeGWASLab()


@pytest.fixture
def input_file(tmp_path: Path) -> Path:
    path = tmp_path / "input.tsv"
    path.write_text(TOY_TSV, encoding="utf-8")
    return path


@pytest.fixture
def valid_config(input_file: Path):
    """A minimal configuration mapping that should validate successfully."""

    def _make(**overrides):
        config = {
            "input": {"path": str(input_file), "format": "gwaslab", "other_columns": ["NOTE"]},
            "reference": {"genome_build": "hg19"},
            "harmonization": {
                "basic_check": True,
                "threads": 1,
                "remove": False,
                "maf_threshold": 0.40,
                "ref_maf_threshold": 0.40,
            },
            "output": {
                "directory": str(input_file.parent / "results"),
                "filename": "harmonized.tsv",
                "save_format": "gwaslab",
            },
        }
        for key, value in overrides.items():
            config[key] = value
        return config

    return _make
