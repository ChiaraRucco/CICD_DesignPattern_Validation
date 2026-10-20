# EADF Design Pattern – Validation Prototype

Companion repository for the paper describing the **Environment-Agnostic Deployment Framework (EADF)** design pattern for CI/CD of data components. It contains a prototype resolver and the experiment scripts and stored results used in the paper's evaluation.

## Scope of the evidence

Please read this section before interpreting any result.

- **This is a controlled, local filesystem simulation.** No experiment calls a cloud API. A "deployment" means the resolver writes JSON artifacts, state files, backups and logs into `environments/<env>/` on the local disk. Cloud operations such as ADF publish or Synapse/Databricks calls appear only as log messages and dispatch labels.
- **Four Azure-configured environments.** The environment catalog [ci/env/environments.yaml](ci/env/environments.yaml) defines `dev`, `sit`, `uat` and `prod`, all with `cloud: azure`, `region: westeurope`.
- **One illustrative AWS descriptor.** The catalog also contains a `prod_aws` entry (Step Functions / S3 / Glue). It shows how a non-Azure target would be described. No experiment deploys to it. Experiment 2 reads it, and it accounts for all of that experiment's EADF drift count (see below).
- **No GCP target.** The repository has no GCP configuration and no GCP execution. Azure, AWS and GCP are presented in the paper as intended instantiations of the pattern, not as validated live targets.
- **Simulated side effects.** The notification and data-quality mix-ins, the smoke tests and the failure injection are all simulated in-process.

## Requirements and setup

- Python 3.11 or 3.12. The recorded campaign used CPython 3.11; reproduction was re-checked with Python 3.12.10 on Windows 11.
- The dependencies are pinned in [requirements.txt](requirements.txt): PyYAML, Jinja2 and MarkupSafe. Everything else is standard library.

```bash
git clone https://github.com/ChiaraRucco/CICD_DesignPattern_Validation.git
cd CICD_DesignPattern_Validation
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

**Windows notes**

- Set UTF-8 mode first: `set PYTHONUTF8=1` (cmd) or `$env:PYTHONUTF8=1` (PowerShell). Without it, experiment 9 fails with a `UnicodeDecodeError` when it reads the YAML mix-in files under the cp1252 locale.
- Clone into a short path. Some generated files (provenance ledgers, backups) have long names. Under deep paths, Windows' 260-character limit causes `FileNotFoundError` in experiments 7, 9 and 10.

## Running the experiments

All commands must be run from the repository root, because the scripts use relative paths.

**Entry point:** [run_all_experiments.py](run_all_experiments.py). It is an interactive runner that runs experiments 1–11 in order, each as a subprocess. It then writes `results/execution_report.json`, regenerates `results/dashboard.html` and opens the dashboard in a browser.

```bash
python run_all_experiments.py          # menu: Enter/0 = all, then confirm with y
printf '0\ny\n' | python run_all_experiments.py   # non-interactive (bash)
```

Single experiments can be run directly, for example `python experiments/1_stage_coverage.py`.

> **Re-running overwrites the committed results.** Experiments write into `results/` and `environments/`, and add new provenance ledgers and backups on each run. To keep the stored campaign intact, run on a fresh clone, or use `git stash` / `git checkout -- results environments` afterwards.

## Repository layout

| Path | Content |
|---|---|
| `eadf_core/` | Prototype: `resolver.py` (7-stage resolver), `deployment_engine.py` (promotion and failure injection), `environment_simulator.py` (filesystem "environments"), `mixin_executor.py`, `component_type_dispatcher.py`, `dashboard_generator.py` |
| `ci/env/environments.yaml` | Environment catalog: 4 Azure environments and the illustrative `prod_aws` descriptor |
| `ci/pattern/` | Pipeline, promotion and mix-in definitions (`notifications`, `data_quality`) |
| `components/` | Four example component specifications: 2 ADF pipelines, 1 dbt project, 1 Databricks notebook |
| `experiments/` | Experiments 1–11 |
| `artifacts/`, `environments/` | Build artifacts and simulated environment state produced by the runs |
| `results/` | Stored outputs (see below) |

## Recorded campaign and result files

The campaign reported in the paper is the full run recorded in **`results/execution_report.json`**, dated **2025-10-29 14:07:44**. It ran 11 experiments: **10 succeeded and 1 failed** (experiment 6, Multi-Environment Deployment).

| # | Script | Output file | What it actually checks | Stored result |
|---|---|---|---|---|
| 1 | `1_stage_coverage.py` | `stage_coverage.json` | Which of the 7 resolver stages execute for one ADF component in `dev` | **6/7** stages (85.7%); `provenance` is reported as not executed |
| 2 | `2_config_drift.py` | `config_drift_results.json` | Counts missing or renamed parameter keys. Baseline: two hand-written per-env configs. EADF: every catalog entry compared against `dev` | Baseline 6, EADF 20, **−233.33%**. All 20 come from `prod_aws`, which lacks keys present in `dev`; the four Azure entries have 0 |
| 3 | `3_velocity.py` | `velocity_metrics.json` | Wall-clock time of 10 local resolver executions, compared with a fixed `baseline_time = 0.5` s constant | Mean ≈ 0.0036 s, median ≈ 0.0023 s, 100% success. The baseline is a constant, not a measurement, and timings vary between runs |
| 4 | `4_late_binding.py` | `late_binding_results.json` | Environment-specific parameters resolved at runtime for `dev`, `sit` and `prod` | Distinct ADF factory and resource group bound per environment |
| 5 | `5_provenance.py` | `provenance_audit.json`, `provenance/*.json` | Presence of **5 top-level sections** (`component`, `environment`, `pipeline`, `stages`, `outcomes`) in the ledger | 5/5 present |
| 6 | `6_deployment_success.py` | `deployment_success.json` | Promotion of 4 components through dev → sit → uat → prod | **Failed in the campaign.** See the note below |
| 7 | `7_deployment_failures.py` | `deployment_failures.json` | Injected smoke-test, gate and deployment failures | Promotions blocked by gates; injected deployment failure in `prod` recorded. **No rollback/restore is recorded** |
| 8 | `8_environment_state.py` | `environment_inspection.json` | Files and state written under `environments/` | 4 components in `dev`; state, logs and backups present |
| 9 | `9_mixin_composition.py` | `mixin_composition.json` | Combinations of simulated mix-ins | Mix-ins applied as requested; notifications are simulated |
| 10 | `10_component_types.py` | `component_type_branching.json` | The **dispatch labels** chosen per component type (ADF, dbt, Databricks) | Expected labels selected. No dbt or Databricks deployment handler is implemented or executed |
| 11 | `11_complexity_metrics.py` | `complexity_metrics.json` | Static LOC and cyclomatic complexity of the EADF resolver and configuration | EADF: **750 code lines** (resolver 431 and YAML configuration 319); resolver **complexity 65**. The Jenkins, GitHub Actions and per-environment-script figures are **hard-coded estimates** in the script, not measured from real implementations |

### Note on experiment 6 and `deployment_success.json`

In the 2025-10-29 14:07 campaign, experiment 6 exited with a non-zero code and wrote no output file. Re-running the committed script reproduces this. All four components stop at their first `dev` deployment, and the script then crashes with `TypeError: object of type 'int' has no len()` (`experiments/6_deployment_success.py`, line 185) before it saves its results. The `results/deployment_success.json` in the repository is therefore **not** from that campaign. It comes from an earlier run on **2025-10-28 19:59**, made with an earlier version of the script that used a different output schema. That run deployed `customer_orders_pipeline` to `dev`, had the `dev → sit` promotion blocked by the gate, and ended with `"status": "failed", "stopped_at": "sit"`. `results/deployment_log_success.json` contains the matching `dev` deployment record. The current script reproduces the same crash.

### Files not produced by the recorded campaign

| File | Origin | Status |
|---|---|---|
| `results/VALIDATION_REPORT.txt` | Earlier run (2025-10-28 19:17), from a report script that is not in this repository | **Superseded.** Its summary lines, such as "drift eliminated (100%)" and "multi-environment deployment validated", contradict its own numbers and are not used in the paper |
| `results/dashboard.html` | Generated at the end of the 14:07 campaign by `eadf_core/dashboard_generator.py` | Some headline cards and the checklist ("100% reduction", "67%", "… validated") are **fixed text in the generator**, not values read from results. Use the JSON files, not the dashboard, as the source of numbers |
| `results/deployment_success.json`, `results/deployment_log_success.json` | 2025-10-28 19:59 run | See the experiment 6 note above |

## Reproduction check

On 2026-10-20 the full sequence was re-run on a fresh copy of this commit (Python 3.12.10, PyYAML 6.0.3, Jinja2 3.1.6, Windows 11, `PYTHONUTF8=1`, short path). It reproduced the recorded outcome: experiments 1–5 and 7–11 succeed and experiment 6 fails with the same `TypeError`. Stage coverage (6/7), drift (6 vs 20, −233%), provenance (5/5 sections) and complexity (431 + 319 code lines, complexity 65) match the stored values. Velocity timings differ, as expected for wall-clock measurements.

## Limitations

- Every deployment, promotion, notification and failure is simulated on the local filesystem. There is no live cloud execution.
- There is no restore-on-rollback evidence, and no type-specific deployment handlers are implemented for dbt or Databricks.
- The velocity baseline and the comparator complexity figures are constants or estimates coded into the scripts.
