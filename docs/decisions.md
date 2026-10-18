# Decisions and known limitations

This page records deliberate choices, things that were verified, and things that
could not be completed in the development environment. Reading it first will
save time.

## 1. Target API: GWASLab 4.2.3, with two documentation drifts

The workflow was written against **GWASLab 4.2.3**. The signatures used here
were read directly from the published wheel source rather than assumed, because
older GWASLab documentation is out of date in at least two places.

### `harmonize(threads=...)`, not `harmonize(n_cores=...)`

Many third-party tutorials and older GWASLab docs pass `n_cores=` to
`Sumstats.harmonize`. In 4.2.3 the parameter is **`threads`**. This repository
uses `threads` (config key `harmonization.threads`). If you copy snippets from
older sources, expect `TypeError: harmonize() got an unexpected keyword
argument 'n_cores'`.

### `get_path()` does not download; `download_ref()` does

Some docs imply that `gl.get_path(name)` fetches a resource. In 4.2.3:

- `gl.get_path(name, ...)` only resolves a **local** path and returns `False`
  when the resource is absent.
- `gl.download_ref(name, directory=None, ...)` performs the download.

`docs/reference_data.md` uses `download_ref`.

Other signatures confirmed in 4.2.3:

- `gl.Sumstats(sumstats, fmt=..., other=[...], build=..., ...)`
- `Sumstats.harmonize(basic_check=..., ref_seq=..., ref_rsid_tsv=...,
  ref_rsid_vcf=..., ref_infer=..., ref_alt_freq=..., ref_maf_threshold=...,
  maf_threshold=..., threads=..., remove=..., ...)`
- `Sumstats.summary()`, `Sumstats.lookup_status(status="STATUS")`,
  `Sumstats.to_format(path, build=None, verbose=True, **kwargs)`

**Dependency pin:** `pyproject.toml` requires `gwaslab>=4.2.3,<5`. If a future
4.x release renames a parameter, this pin should be reviewed.

## 2. License: DECISION PENDING (deliberately not chosen)

No license is asserted. The `LICENSE` file states this explicitly. The reason is
that the repository redistributes `data/to_harmonize.tsv`, which comes from
GWASLab (**GPL-3.0-only**), while the original code could be licensed more
permissively. Because license choice is legally meaningful, it is left to the
repository owner. The two most reasonable options (GPL-3.0-only, or MIT with the
data attribution preserved) are described in `LICENSE`. **Do not assume reuse
rights until a license is selected.**

## 3. GWASLab/pysam could not be installed in the development environment

Attempting to install GWASLab in the development environment failed because its
native dependency `pysam` (htslib) does not build here:

```
hts.c:157:27: error: incomplete universal character name \U
```

This is a GCC 15 + htslib issue: `htslib`'s generated `config_vars.h` embeds a
Windows path containing `\U`, which GCC 15 rejects as an incomplete universal
character name. It reproduces with pysam 0.22.1 and 0.24.1 on this machine, and
no prebuilt pysam wheel was available from the configured package index.

**Consequences:**

- The notebook has **not** been executed here, and no scientific integration
  test was run against real reference data. See item 5.
- To use the workflow, install GWASLab in an environment where pysam builds or a
  wheel is available (typically Linux/macOS, or a Windows machine with an
  older MSVC/GCC toolchain). The workflow code itself is not affected.

## 4. Testing strategy: GWASLab is injected, not imported

Because GWASLab cannot be installed here, the test-suite does not import it.
`run_harmonization(config, gl=...)` accepts the GWASLab module, so tests pass a
fake module that records calls. This keeps CI fast, dependency-light and
deterministic, and it pins down exactly which GWASLab arguments the workflow
sends. The trade-off is that tests verify **control flow and argument mapping**,
not GWASLab's scientific behaviour.

## 5. The notebook is a tutorial, not a validated result set

`notebooks/01_harmonization_workflow.ipynb` walks through the workflow with the
toy dataset and explains each step. Any numbers in it are illustrative of the
tooling and are **not** measured results, because it has not been executed
against real reference data. Re-run it locally after installing GWASLab and
downloading references (see `docs/reference_data.md`).

## 6. Path handling

Relative paths in the config are resolved against `base_dir`, which defaults to
the current working directory (expected to be the repository root) and can be
overridden via `--base-dir`. This keeps the repository portable across machines
and operating systems. Reference resources are expected to live outside the
repository and are git-ignored.

## 7. Relation to the standardization repository

This repository is the harmonization-focused companion to
`gwaslab-standardization` (a sibling repository by the same author). They share
conventions (config style, tests, docs) but are independent: standardization
cleans up input columns, whereas this repository performs reference-based
harmonization. Do not modify the standardization repository from here.
