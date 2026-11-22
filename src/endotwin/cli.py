"""Command-line entry point: ``python -m endotwin.cli <command>``.

``all`` regenerates every committed ENDO-TWIN result under
``endotwin/results/<model_version>/`` and the figures under
``docs/assets/endotwin/``, then the research-foundation metrics. Each results
directory carries ``run_manifest.json`` with the SHA-256 of every model and
configuration file it was computed from, so a result is bound to content rather
than to a commit.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from endotwin import DEFAULT_MODEL_VERSION
from endotwin.model import load_model, sha256_file
from endotwin.paths import CONFIG, EVIDENCE, RESULTS, relative
from endotwin.protocols import load_protocols
from endotwin.simulate import (
    SimulationSettings,
    engine_report,
    model_file_digests,
    simulate_condition,
)

CONFIRM_SAMPLES = 2000
REFERENCE_SAMPLES = 10000


def _write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def results_dir(version: str) -> Path:
    return RESULTS / version


def input_digests(model) -> dict[str, str]:
    files = {f"model/{k}": v for k, v in model_file_digests(model).items()}
    for name in ("protocols.yaml", "interventions.tsv", "observation_map.tsv"):
        files[f"config/{name}"] = sha256_file(CONFIG / name)
    files["evidence/references.tsv"] = sha256_file(EVIDENCE / "references.tsv")
    return files


def cmd_structure(args) -> None:
    from endotwin.structure import summarize

    model = load_model(args.model)
    out = results_dir(model.version)
    summary = summarize(model.rules, model.outputs, model.readout_nodes).as_dict()
    per_variant = {}
    for selection in model.scenarios():
        label = "+".join(selection[f] for f in sorted(selection))
        s = summarize(model.rules_for(selection), model.outputs, model.readout_nodes)
        per_variant[label] = {
            "distinct_functions": s.distinct_functions,
            "dependencies": s.dependencies,
            "alias_classes": [list(c) for c in s.alias_classes],
            "phenotype_inert_nodes": list(s.phenotype_inert_nodes),
        }
    _write_json(
        out / "structure.json",
        {"model_version": model.version, "default": summary, "scenarios": per_variant},
    )
    print(f"wrote {relative(out / 'structure.json')}")


def cmd_predict(args) -> None:
    from endotwin.analysis import (
        comparison_directions,
        discrimination_table,
        exact_predictions,
    )

    model = load_model(args.model)
    protocols = load_protocols(model)
    out = results_dir(model.version)
    rows = exact_predictions(model, protocols)
    directions = comparison_directions(model, protocols, rows)
    _write_tsv(out / "fixed_point_predictions.tsv", rows)
    _write_tsv(out / "comparison_directions.tsv", directions)
    _write_tsv(
        out / "discrimination.tsv", discrimination_table(model, protocols, directions)
    )
    print(
        f"wrote exact predictions for {len(model.scenarios())} rule-variant scenarios"
    )


def cmd_confirm(args) -> None:
    from endotwin.analysis import exact_predictions, maboss_confirmation

    model = load_model(args.model)
    protocols = load_protocols(model)
    settings = SimulationSettings(sample_count=args.samples, seed=args.seed)
    rows = maboss_confirmation(
        model, protocols, settings, exact_predictions(model, protocols)
    )
    out = results_dir(model.version)
    _write_tsv(out / "maboss_confirmation.tsv", rows)
    worst = max(r["max_abs_deviation_from_exact"] for r in rows)
    unconverged = sum(1 for r in rows if not r["converged"])
    _write_json(
        out / "maboss_confirmation_summary.json",
        {
            "records": len(rows),
            "unconverged_phases": unconverged,
            "max_abs_deviation_from_exact_fixed_point": worst,
            "sample_count": args.samples,
            "seed": args.seed,
        },
    )
    print(
        f"confirmation: {len(rows)} phase records, worst deviation {worst}, unconverged {unconverged}"
    )


def cmd_transient(args) -> None:
    from endotwin.analysis import relay_transient

    model = load_model(args.model)
    protocols = load_protocols(model)
    result = relay_transient(
        model, protocols, replicates=args.replicates, sample_count=args.samples
    )
    out = results_dir(model.version)
    rows = [
        {
            "time_in_phase": t,
            "relay_mean": round(a, 6),
            "relay_sd": round(b, 6),
            "relay_plus_direct_mean": round(c, 6),
            "relay_plus_direct_sd": round(d, 6),
            "difference": round(a - c, 6),
        }
        for t, a, b, c, d in zip(
            result.time,
            result.mean_relay,
            result.sd_relay,
            result.mean_direct,
            result.sd_direct,
            strict=True,
        )
    ]
    _write_tsv(out / "relay_transient.tsv", rows)
    _write_json(out / "relay_transient_summary.json", result.summary)
    print(json.dumps(result.summary, indent=2))


def cmd_rates(args) -> None:
    from endotwin.analysis import (
        comparison_directions,
        rate_sensitivity,
        relay_rate_robustness,
    )

    model = load_model(args.model)
    protocols = load_protocols(model)
    out = results_dir(model.version)
    rows, summary = rate_sensitivity(
        model, protocols, comparison_directions(model, protocols), samples=args.samples
    )
    _write_tsv(out / "rate_sensitivity.tsv", rows)
    relay_rows, relay_summary = relay_rate_robustness(
        model, protocols, samples=args.relay_samples
    )
    _write_tsv(out / "relay_rate_robustness.tsv", relay_rows)
    summary["relay_transient_under_random_rates"] = relay_summary
    _write_json(out / "rate_sensitivity_summary.json", summary)
    print(json.dumps(summary, indent=2))


def cmd_reference(args) -> None:
    model = load_model(args.model)
    protocols = load_protocols(model)
    out = results_dir(model.version)
    settings = SimulationSettings(sample_count=args.samples, seed=args.seed)
    runs = [
        (condition_id, variant)
        for condition_id in ("reference", "bmpr_inhibition")
        for variant in (None, "Q1_pgr_sufficient")
    ] + [
        ("il1b_exposure", None),
        ("il1b_exposure", "INF_pgr_depletion"),
        ("foxo1_inhibition", None),
        ("foxo1_inhibition", "FOX_prl_foxo1_independent"),
    ]
    for condition_id, variant in runs:
        selection = model.selection_from_ids([variant]) if variant else None
        result = simulate_condition(
            model,
            protocols.conditions[condition_id],
            protocols.interventions,
            selection,
            settings,
        )
        tag = f"{condition_id}__{variant or 'default'}"
        frame = result.trajectory()
        frame.round(6).to_csv(
            out / f"dynamics_{tag}.tsv", sep="\t", index=False, lineterminator="\n"
        )
        _write_json(out / f"dynamics_{tag}_provenance.json", result.provenance())
    print("wrote reference dynamics")


def cmd_manifest(args) -> None:
    model = load_model(args.model)
    out = results_dir(model.version)
    from endotwin.predictions import git_state

    _write_json(
        out / "run_manifest.json",
        {
            "model_version": model.version,
            "command": "pixi run endotwin-all",
            "inputs_sha256": input_digests(model),
            "engine": engine_report(),
            "repository_state_at_generation": git_state(),
            "outputs": sorted(
                p.name
                for p in out.iterdir()
                if p.is_file() and p.name != "run_manifest.json"
            ),
            "semantics": (
                "MaBoSS probabilities are simulated trajectory frequencies under the stated "
                "rules, unit transition rates (unless stated) and initial conditions; MaBoSS "
                "time is dimensionless and not mapped to experimental time. No result here "
                "is a biological observation or a validation."
            ),
        },
    )
    print(f"wrote {relative(out / 'run_manifest.json')}")


def cmd_figures(args) -> None:
    from endotwin import figures

    figures.render_all(args.model)


def cmd_metrics(args) -> None:
    from endotwin.foundation_metrics import write

    write()
    print("wrote docs/research_foundation_metrics.json")


def cmd_all(args) -> None:
    ns = argparse.Namespace
    m = args.model
    cmd_structure(ns(model=m))
    cmd_predict(ns(model=m))
    cmd_confirm(ns(model=m, samples=CONFIRM_SAMPLES, seed=1))
    cmd_transient(ns(model=m, replicates=10, samples=5000))
    cmd_rates(ns(model=m, samples=30, relay_samples=20))
    cmd_reference(ns(model=m, samples=REFERENCE_SAMPLES, seed=1))
    cmd_figures(ns(model=m))
    cmd_manifest(ns(model=m))
    cmd_metrics(ns(model=m))


def cmd_freeze(args) -> None:
    from endotwin.predictions import freeze

    if not args.check:
        print(relative(freeze(Path(args.spec), allow_dirty=args.allow_dirty)))
        return
    import tempfile

    # Dry run: the full eligibility analysis, written to a throwaway folder.
    with tempfile.TemporaryDirectory() as tmp:
        record = freeze(
            Path(args.spec), out_root=Path(tmp), allow_dirty=True, check_only=True
        )
        payload = json.loads((record / "predictions.json").read_text())
    sens = payload["sensitivity"]
    print(
        json.dumps(
            {
                "prediction_id": payload["prediction_id"],
                "comparison": payload["comparison"]["id"],
                "predictions": payload["predictions"],
                "stable_under_rule_variants": sens["stable_under_rule_variants"],
                "stable_under_rates": sens["stable_under_rates"],
                "stable_under_initial_conditions": sens[
                    "stable_under_initial_conditions"
                ],
                "eligible": sens["eligible"],
                "note": "check only: nothing was frozen",
            },
            indent=2,
        )
    )


def cmd_verify(args) -> None:
    from endotwin.predictions import verify

    report = verify(Path(args.record))
    print(json.dumps(report, indent=2))
    if not report["intact"]:
        sys.exit(1)


def cmd_evaluate(args) -> None:
    from endotwin.predictions import evaluate

    print(relative(evaluate(Path(args.record), Path(args.observations))))


def cmd_validate_data(args) -> None:
    from endotwin.data_interfaces import read_table, validate
    from endotwin.observations import load_observation_map

    model = load_model(args.model)
    report = validate(
        args.schema, read_table(Path(args.table)), load_observation_map(model)
    )
    print(
        json.dumps(
            {"table": report.table, "rows": report.rows, "errors": report.errors},
            indent=2,
        )
    )
    if not report.ok:
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="endotwin")
    parser.add_argument("--model", default=DEFAULT_MODEL_VERSION)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("structure").set_defaults(func=cmd_structure)
    sub.add_parser("predict").set_defaults(func=cmd_predict)
    p = sub.add_parser("confirm")
    p.add_argument("--samples", type=int, default=CONFIRM_SAMPLES)
    p.add_argument("--seed", type=int, default=1)
    p.set_defaults(func=cmd_confirm)
    p = sub.add_parser("transient")
    p.add_argument("--replicates", type=int, default=10)
    p.add_argument("--samples", type=int, default=5000)
    p.set_defaults(func=cmd_transient)
    p = sub.add_parser("rate-sensitivity")
    p.add_argument("--samples", type=int, default=30)
    p.add_argument("--relay-samples", type=int, default=20)
    p.set_defaults(func=cmd_rates)
    p = sub.add_parser("reference-dynamics")
    p.add_argument("--samples", type=int, default=REFERENCE_SAMPLES)
    p.add_argument("--seed", type=int, default=1)
    p.set_defaults(func=cmd_reference)
    sub.add_parser("manifest").set_defaults(func=cmd_manifest)
    sub.add_parser("figures").set_defaults(func=cmd_figures)
    sub.add_parser("metrics").set_defaults(func=cmd_metrics)
    sub.add_parser("all").set_defaults(func=cmd_all)
    p = sub.add_parser("freeze")
    p.add_argument("spec")
    p.add_argument("--allow-dirty", action="store_true")
    p.add_argument(
        "--check",
        action="store_true",
        help="run the eligibility analysis without writing a frozen record",
    )
    p.set_defaults(func=cmd_freeze)
    p = sub.add_parser("verify-frozen")
    p.add_argument("record")
    p.set_defaults(func=cmd_verify)
    p = sub.add_parser("evaluate")
    p.add_argument("record")
    p.add_argument("observations")
    p.set_defaults(func=cmd_evaluate)
    p = sub.add_parser("validate-data")
    p.add_argument(
        "schema",
        choices=[
            "bulk_rnaseq_samples",
            "functional_measurements",
            "deconvolution_estimates",
        ],
    )
    p.add_argument("table")
    p.set_defaults(func=cmd_validate_data)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
