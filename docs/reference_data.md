# Reference data

Reference-based harmonization needs at least one reference resource. These files
are large and are **not** committed to this repository. This page explains what
each resource is for and how to obtain it.

## Which resource do I need?

| Goal | Resource | Config field | GWASLab key (examples) |
| --- | --- | --- | --- |
| Verify REF/ALT alleles and flip strands against the reference genome | Reference FASTA | `reference.fasta_path` | `ucsc_genome_hg19`, `ucsc_genome_hg38` |
| Infer strand for palindromic SNPs from reference allele frequencies | Reference VCF/BCF with AF | `reference.inference_vcf_path` + `reference.allele_frequency_field` | `1kg_eas_hg19`, `1kg_eur_hg19` |
| Check/assign rsIDs | rsID reference | `reference.rsid_tsv_path` / `reference.rsid_vcf_path` | `1kg_dbsnp151_hg19_auto` (TSV) |

If you set **neither** a FASTA nor an inference VCF, the workflow still runs but
performs standardization/basic checks only — it is *not* full harmonization. The
validator warns you when this happens.

## Downloading resources with GWASLab

GWASLab can download and cache reference resources. It does **not** download
them implicitly: `gl.get_path(name)` only looks up a local path (and returns
`False` when missing), whereas `gl.download_ref(name)` performs the download and
returns the local path.

```python
import gwaslab as gl

fasta = gl.download_ref("ucsc_genome_hg19")  # reference FASTA
vcf = gl.download_ref("1kg_eas_hg19")  # EAS 1000G allele frequencies
print(fasta, vcf)
```

By default GWASLab stores these under your user profile (`~/.gwaslab`). You can
also download to an explicit directory:

```python
gl.download_ref("ucsc_genome_hg19", directory="/path/to/reference")
```

See the official GWASLab documentation for the full list of resource keys. The
keys above were confirmed against GWASLab 4.2.3's bundled `reference.json`.

## Pointing the configuration at downloaded resources

Set the absolute paths in `config/harmonization.yaml`:

```yaml
reference:
  genome_build: hg19
  fasta_path: /path/to/hg19.fa
  inference_vcf_path: /path/to/eas_1kg.vcf.gz
  allele_frequency_field: AF
```

Notes and gotchas:

- **Index files.** An inference VCF/BCF needs a tabix (`.tbi`) or CSI (`.csi`)
  index next to it; GWASLab's random access relies on it. Downloads via
  `download_ref` usually include the index.
- **Build matching.** The reference build must match the data's build. The
  workflow passes the build code to GWASLab but does **not** validate that a
  FASTA is really hg19 — supplying a mismatched build is a silent scientific
  error, so double-check it.
- **Disk and memory.** A human reference FASTA is a few GB; whole-genome VCFs
  are much larger. Prefer BCF + CSI when available to save space.
- **Do not commit them.** These paths are covered by `.gitignore`.

## Reproducibility

The run manifest records which reference paths were actually used, together
with their roles, so a result can be traced back to specific resource files.
Because reference files are not hash-pinned here, record the download date or
your own checksums if you need bit-for-bit reproducibility. See
`docs/results.md`.
