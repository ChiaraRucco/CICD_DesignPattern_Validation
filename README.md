# EADF Design Pattern – Validation Prototype

Companion repository for the paper describing the **Environment-Aware Deployment Framework (EADF)** design pattern for CI/CD of data components. It contains a prototype resolver and the experiment scripts and stored results used in the paper's evaluation.

## Scope of the evidence

Please read this section before interpreting any result.

- **This is a controlled, local filesystem simulation.** No experiment calls a cloud API. A "deployment" means the resolver writes JSON artifacts, state files, backups and logs into `environments/<env>/` on the local disk. Cloud operations such as ADF publish or Synapse/Databricks calls appear only as log messages and dispatch labels.
- **Four Azure-configured environments.** The environment catalog [ci/env/environments.yaml](ci/env/environments.yaml) defines `dev`, `sit`, `uat` and `prod`, all with `cloud: azure`, `region: westeurope`.
- **One illustrative AWS descriptor.** The catalog also contains a `prod_aws` entry (Step Functions / S3 / Glue). It shows how a non-Azure target would be described. No experiment deploys to it. Experiment 2 reads it, and it accounts for all of that experiment's EADF drift count (see below).
- **No GCP target.** The repository has no GCP configuration and no GCP execution. Azure, AWS and GCP are presented in the paper as intended instantiations of the pattern, not as validated live targets.
- **Recorded inputs, not measurements.** Gate outcomes, smoke-test results and data-quality checks come from the evidence files supplied with each component. Those files are labelled synthetic. Notifications are logged, and failure injection is simulated in-process.

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

**Entry point:** [run_all_experiments.py](run_all_experiments.py). It is an interactive runner that runs experiments 1–11 in order, each as a subprocess. It then writes `results/execution_report.json`, regenerates `results/dashboard.html` and opens the dashboard in a browser. The dashboard's headline cards are fixed text in the generator (see below), so take numbers from the JSON files.

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
| `tests/` | Unit tests for gates, smoke tests, validation, and determinism |
| `artifacts/`, `environments/` | Build artifacts and simulated environment state produced by the runs |
| `results/` | Stored outputs (see below) |

## Current campaign and result files (evidence-based revision, 2026-11-23)

The stored results in `results/` and `environments/` come from the evidence-based revision of the prototype. The previous campaign (2025-10-28/29, with a random gate model) is in git history at commit `63044e3` and is not evidence for the current code.

Run the campaign with:

```bash
printf '0\ny\n' | python run_all_experiments.py
```

All eleven scripts exit with status 0. The runner reports exit status, not the validation checks inside each experiment. Some of those checks report FAIL, as listed below.

**Inputs that drive the outcomes**

- Gates and smoke tests read `components/<name>/evidence.yaml`. Automated gates pass only when the file records `passed` for the gate in the current environment. Manual gates pass only when the file names an approver. A missing value fails the gate (`not_evaluated` or `pending_approval`) and blocks promotion.
- The four example evidence files are labelled **SYNTHETIC DEMO INPUTS**. They are controlled test inputs, not records of real tests or approvals. Removing a value from one of them makes the corresponding gate fail closed.
- Promotion rules are read from the keys of `ci/pattern/promotion.yaml` (`<from>_to_<to>`).
- Dependencies must be components in this repository at or above `min_version`. Dependencies outside the repository fail validation.
- Target clouds are declared per component type in `SUPPORTED_TARGETS` (`eadf_core/resolver.py`).

**What is still simulated**

- Azure and AWS deployment calls only log; no cloud API is called. Provenance records `execution_mode: simulated`.
- Vault references resolve to `MOCK_SECRET_*` strings. Provenance records `secret_resolution: mock`.
- Notifications are logged, not sent.

| # | Script | Output file | What it checks | Stored result |
|---|---|---|---|---|
| 1 | `1_stage_coverage.py` | `stage_coverage.json` | Which of the 7 resolver stages execute for one ADF component in `dev` | **6/7** stages; `provenance` is reported as not executed |
| 2 | `2_config_drift.py` | `config_drift_results.json` | Counts missing parameter keys. Baseline: two hand-written per-environment configs. EADF: every catalog entry compared with `dev` | Baseline **6**, EADF catalog **20** (all from the illustrative `prod_aws` entry). No percentage is reported, because the two counts are not comparable |
| 3 | `3_velocity.py` | `velocity_metrics.json` | Wall-clock time of 10 local resolver runs | Median ≈ 0.00055 s. The 0.5 s "baseline" is a constant in the script; no improvement is reported against it |
| 4 | `4_late_binding.py` | `late_binding_results.json` | Environment-specific parameters resolved at runtime for `dev`, `sit`, `prod` | Distinct factory and resource group bound per environment |
| 5 | `5_provenance.py` | `provenance_audit.json`, `provenance/*.json` | Presence of the 5 top-level sections in the record | 5/5 present |
| 6 | `6_deployment_success.py` | `deployment_success.json` | Promotion of 4 components through dev, sit, uat, prod | **3 of 4** complete the chain (`analytics_dbt`, `customer_orders_pipeline`, `ml_training_notebook`). `inventory_sync_pipeline` fails validation because its dependencies are outside the repository. Validation checks "All components deployed" and "Environment consistency" report **FAIL** |
| 7 | `7_deployment_failures.py` | `deployment_failures.json` | Injected smoke-test, gate, and deployment failures | Failures recorded and promotions blocked. No rollback is recorded in the failure records |
| 8 | `8_environment_state.py` | `environment_inspection.json` | Files and state written under `environments/` | Components and state present in each environment |
| 9 | `9_mixin_composition.py` | `mixin_composition.json` | Combinations of mix-ins | Notifications are logged. Data-quality checks report `not_evaluated` because this experiment supplies no evidence, so the data-quality validation reports **FAIL** |
| 10 | `10_component_types.py` | `component_type_branching.json` | Dispatch labels chosen per component type | Labels selected as declared. No dbt or Databricks deployment handler exists |
| 11 | `11_complexity_metrics.py` | `complexity_metrics.json` | Static size and cyclomatic complexity of the resolver and the configuration | Resolver **477** code lines, complexity **85**; configuration **319** code lines. Three comparison checks against the Jenkins, GitHub Actions, and script baselines report **FAIL**. Those baselines are hard-coded estimates in the script |

Experiment 6 checks two items that fail, as described above. Experiment 9 has one check that fails (data quality, no evidence supplied). Experiment 11 checks three comparisons that fail. All are reported as they are.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests check that gates fail closed without evidence, that promotion rules come from `promotion.yaml`, that smoke tests report `not_run` without a recorded value, that validation fails for out-of-repository dependencies and undeclared target clouds, that provenance lists only checks that ran, and that repeated runs of the same promotion give the same outcome.

## Reproduction check

The 2026-10-20 reproduction applied to commit `63044e3` and its random gate model. It does not apply to the current code. A reproduction of the current campaign should be run on a fresh clone with the commands above.

## Limitations

- Every deployment, notification, and secret is simulated on the local filesystem. There is no live cloud execution.
- Gate and smoke-test outcomes are only as good as the evidence files supplied. The included files are synthetic and exist to exercise the logic, not to show that any component is safe to promote.
- There is no restore-on-rollback evidence, and no deployment handlers exist for dbt or Databricks.
- The comparator complexity figures and the velocity baseline are constants or estimates coded into the scripts.
