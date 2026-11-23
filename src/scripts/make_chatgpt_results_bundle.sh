#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# src/scripts/ -> repo root is two levels up (moved from scripts/ on 2026-11-23).
repo_root="$(cd "$script_dir/../.." && pwd -P)"
cd "$repo_root"

# The harness (AGENTS.md, agents, skills, harness docs, validator) is part of
# how this repository is meant to be read, so a reviewer gets it by default.
include_harness=1
bundle=""
smoke_run_override=""
max_file_bytes=$((20 * 1024 * 1024))
max_bundle_bytes=$((60 * 1024 * 1024))

usage() {
    cat <<'EOF'
Usage: src/scripts/make_chatgpt_results_bundle.sh [options]

Create a compact, validated archive for sharing DT_ADOC source, documentation,
scientific context, models, and available result files with ChatGPT.

Options:
  --include-harness  Include AGENTS.md and repository-local Codex harness files
                     (default).
  --no-harness       Omit the harness files.
  --smoke-run PATH   Bundle this specific smoke run directory instead of the
                     one with the newest run_manifest.json.
  --output PATH      Write the archive to PATH. The path must not already exist.
  -h, --help         Show this help message.

Raw source data, papers, office documents, caches, checkpoints, and files larger
than 20 MiB are excluded. The small ADOC protein-readout workbook is the sole
office-document exception and is accompanied by full TSV exports. The completed
archive may not exceed 60 MiB.
EOF
}

while (($#)); do
    case "$1" in
        --include-harness)
            include_harness=1
            ;;
        --no-harness)
            include_harness=0
            ;;
        --smoke-run)
            shift
            if (($# == 0)); then
                printf 'Missing value for --smoke-run\n' >&2
                exit 2
            fi
            smoke_run_override="$1"
            ;;
        --output)
            shift
            if (($# == 0)); then
                printf 'Missing value for --output\n' >&2
                exit 2
            fi
            bundle="$1"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

mkdir -p output/reports
if [ -z "$bundle" ]; then
    bundle="output/reports/chatgpt_results_$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
elif [[ "$bundle" != /* ]]; then
    bundle="$repo_root/$bundle"
fi

if [ -e "$bundle" ]; then
    printf 'Refusing to overwrite existing output: %s\n' "$bundle" >&2
    exit 1
fi

stage="$(mktemp -d)"
trap 'rm -rf -- "$stage"' EXIT
bundle_root="$stage/DT_ADOC_chatgpt_bundle"
manifest_rows="$stage/manifest_rows.tsv"
mkdir -p "$bundle_root"
: > "$manifest_rows"

sha256_file() {
    sha256sum "$1" | awk '{print $1}'
}

is_forbidden_path() {
    local path="$1"
    case "/$path/" in
        */.git/*|*/.pixi/*|*/.venv/*|*/__pycache__/*|*/.pytest_cache/*|*/.mypy_cache/*|*/.ruff_cache/*|*/.ipynb_checkpoints/*|*/cache/*|*/checkpoints/*|*/tmp/*)
            return 0
            ;;
    esac
    case "$path" in
        *.pyc|*.pyo|*.pyd|*.rds|*.Rds|*.RData|*.rda|*.h5ad|*.h5|*.loom|*.pkl|*.pickle|*.pdf|*.docx|*.xlsx|*.xls|*.zip|*.tar|*.tar.gz|*.tgz)
            return 0
            ;;
    esac
    return 1
}

is_eligible_source() {
    local path="$1"
    case "$path" in
        *.md|*.txt|*.tsv|*.csv|*.json|*.toml|*.lock|*.yaml|*.yml|*.py|*.R|*.r|*.sh|*.bnd|*.cfg|*.xml|*.sbml|*.gitignore|*.gif|*.png|*.mmd)
            return 0
            ;;
    esac
    return 1
}

is_eligible_result() {
    local path="$1"
    case "$path" in
        *.md|*.txt|*.tsv|*.csv|*.json|*.yaml|*.yml|*.bnd|*.cfg|*.log|*.tsv.gz|*.csv.gz|*.json.gz|*.txt.gz|*.gif|*.png)
            return 0
            ;;
    esac
    return 1
}

record_manifest_row() {
    local relative_path="$1"
    local reason="$2"
    local staged="$bundle_root/$relative_path"
    printf '%s\t%s\t%s\t%s\n' \
        "$relative_path" \
        "$(stat -c '%s' "$staged")" \
        "$(sha256_file "$staged")" \
        "$reason" \
        >> "$manifest_rows"
}

copy_file() {
    local path="$1"
    local reason="$2"
    local profile="${3:-source}"
    local size_bytes

    [ -f "$path" ] || return 0
    is_forbidden_path "$path" && return 0
    if [ "$profile" = "result" ]; then
        is_eligible_result "$path" || return 0
    else
        is_eligible_source "$path" || return 0
    fi
    size_bytes="$(stat -c '%s' "$path")"
    [ "$size_bytes" -le "$max_file_bytes" ] || return 0
    [ ! -e "$bundle_root/$path" ] || return 0

    mkdir -p "$(dirname "$bundle_root/$path")"
    cp -p -- "$path" "$bundle_root/$path"
    record_manifest_row "$path" "$reason"
}

copy_tree() {
    local root="$1"
    local reason="$2"
    local profile="${3:-source}"
    [ -d "$root" ] || return 0
    while IFS= read -r -d '' path; do
        copy_file "$path" "$reason" "$profile"
    done < <(find "$root" -type f -print0 | sort -z)
}

copy_file README.md "project-overview"
# DT-ADOC planning ledgers now live in docs/legacy/ and travel with the docs tree.
copy_file docs/THIRD_PARTY_NOTICES.md "third-party-provenance"
copy_file pixi.toml "runtime-and-task-definition"
copy_file pixi.lock "runtime-lock"
copy_file .gitignore "generated-file-policy"

for root in src scripts models tests; do
    copy_tree "$root" "repo-source"
done
for root in docs context config; do
    copy_tree "$root" "scientific-context-and-configuration"
done
# Canonical annotated input tables. These supersede the workbook and the
# migration prose as the operational source of truth, so a reviewer needs them.
copy_tree input_tables "canonical-input-table"

if [ ! -f "$bundle_root/docs/legacy/REQUIREMENTS_COVERAGE.tsv" ] && [ -f docs/legacy/IMPLEMENTATION_PLAN.md ]; then
    mkdir -p "$bundle_root/docs/legacy"
    PYTHONDONTWRITEBYTECODE=1 python - <<'PY' "$repo_root/docs/legacy/IMPLEMENTATION_PLAN.md" "$bundle_root/docs/legacy/REQUIREMENTS_COVERAGE.tsv"
from pathlib import Path
import sys

plan_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
lines = plan_path.read_text(encoding="utf-8").splitlines()
rows: list[list[str]] = []
in_table = False
for line in lines:
    if line.startswith("| Requirement ID |"):
        in_table = True
        continue
    if in_table and line.startswith("|---"):
        continue
    if in_table and line.startswith("| "):
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) == 6:
            rows.append(parts)
        continue
    in_table = False

target_path.write_text(
    "requirement_id\trequirement\timplementation_phase\texpected_files\tacceptance_test\tstatus\n"
    + "\n".join("\t".join(row) for row in rows)
    + "\n",
    encoding="utf-8",
)
PY
    record_manifest_row "docs/legacy/REQUIREMENTS_COVERAGE.tsv" "implementation-ledger-generated"
fi

if [ "$include_harness" -eq 1 ]; then
    copy_file AGENTS.md "project-agent-policy"
    copy_tree docs/codex/harness "project-scientific-contract"
    copy_tree docs/codex/agents "project-agent-definition"
    copy_tree docs/codex/skills "skill-guidance"
fi

results_present=0
for root in output/results results; do
    if [ -d "$root" ]; then
        results_present=1
        copy_tree "$root" "analysis-result" "result"
    fi
done

latest_smoke_run=""
if [ -n "$smoke_run_override" ]; then
    if [ ! -f "$smoke_run_override/run_manifest.json" ]; then
        printf 'No run_manifest.json under --smoke-run %s\n' "$smoke_run_override" >&2
        exit 2
    fi
    latest_smoke_run="${smoke_run_override%/}"
fi
if [ -z "$latest_smoke_run" ] && [ -d output/smoke ]; then
    # Newest run_manifest.json by mtime. The explicit secondary key makes the
    # choice reproducible when two runs share a timestamp; without it the tie
    # falls back to sort's last-resort whole-line comparison, which is not an
    # ordering anyone reading this script would predict. Use --smoke-run to
    # pin a specific run rather than relying on mtime at all.
    latest_smoke_run="$(
        find output/smoke -type f -name run_manifest.json -print \
        | while IFS= read -r path; do
            printf '%s\t%s\n' "$(stat -c '%Y' "$path")" "$(dirname "$path")"
        done \
        | sort -k1,1nr -k2,2 \
        | awk -F'\t' 'NR == 1 {print $2}'
    )"
fi
if [ -n "$latest_smoke_run" ]; then
    node_probtraj_sample=""
    if [ -d "$latest_smoke_run/raw" ]; then
        node_probtraj_sample="$(
            find "$latest_smoke_run/raw" -type f -name '*_nodes_probtraj.tsv' \
                ! -name '*_last_nodes_probtraj.tsv' -print \
            | while IFS= read -r path; do
                printf '%s\t%s\n' "$(stat -c '%s' "$path")" "$path"
            done \
            | sort -k1,1n -k2,2 \
            | awk -F'\t' 'NR == 1 {print $2}'
        )"
    fi
    if [ -n "$node_probtraj_sample" ]; then
        copy_file "$node_probtraj_sample" "node-probability-trajectory-sample" "result"
    else
        printf 'Note: selected smoke run %s has no full node-probability trajectory (predates trajectory capture).\n' \
            "$latest_smoke_run" >&2
    fi
    copy_tree "$latest_smoke_run" "latest-smoke-run" "result"
fi

# Generated visualization runs: animation metadata plus the raw node-probability
# trajectories the animation was drawn from. Small, and needed to check any
# displayed value against source. The full-resolution GIF is skipped -- the
# README animation is already carried under docs/assets.
if [ -d output/visualization ]; then
    while IFS= read -r path; do
        case "$path" in
            *_full.gif) continue ;;
        esac
        copy_file "$path" "visualization-run-output" "result"
    done < <(find output/visualization -type f | sort)
fi

protein_readout_present=0
protein_workbook="data/proteinas secretadas ADOC.xlsx"
protein_bundle_dir="input_tables/protein_readouts"
if [ -f "$protein_workbook" ]; then
    protein_size="$(stat -c '%s' "$protein_workbook")"
    if [ "$protein_size" -gt $((2 * 1024 * 1024)) ]; then
        printf 'Protein-readout workbook exceeds the 2 MiB allowlist limit: %s\n' \
            "$protein_workbook" >&2
        exit 1
    fi
    mkdir -p "$bundle_root/$protein_bundle_dir"
    cp -p -- "$protein_workbook" \
        "$bundle_root/$protein_bundle_dir/proteinas secretadas ADOC.xlsx"
    record_manifest_row \
        "$protein_bundle_dir/proteinas secretadas ADOC.xlsx" \
        "protein-readout-source-workbook"
    PYTHONDONTWRITEBYTECODE=1 python -B src/scripts/export_protein_readout_tables.py \
        --input "$protein_workbook" \
        --output-dir "$bundle_root/$protein_bundle_dir"
    while IFS= read -r -d '' generated; do
        relative="${generated#"$bundle_root/"}"
        case "$relative" in
            "$protein_bundle_dir/proteinas secretadas ADOC.xlsx")
                continue
                ;;
        esac
        record_manifest_row "$relative" "protein-readout-portable-export"
    done < <(find "$bundle_root/$protein_bundle_dir" -type f -print0 | sort -z)
    protein_readout_present=1
fi

src_present=0
[ -d src ] && src_present=1
models_present=0
if find models -type f \( -name '*.bnd' -o -name '*.cfg' \) -print -quit 2>/dev/null | grep -q .; then
    models_present=1
fi

viz_animation_present=0
[ -f "$bundle_root/docs/assets/adoc_maboss_pathway_dynamics.gif" ] && viz_animation_present=1
viz_preview_present=0
[ -f "$bundle_root/docs/assets/adoc_maboss_pathway_dynamics_preview.png" ] && viz_preview_present=1
viz_metadata_present=0
[ -f "$bundle_root/docs/assets/adoc_maboss_pathway_dynamics_metadata.json" ] && viz_metadata_present=1
viz_trajectory_sample_present=0
if grep -q -F -- $'\tnode-probability-trajectory-sample' "$manifest_rows"; then
    viz_trajectory_sample_present=1
fi
if [ "$viz_animation_present" -eq 1 ] && [ "$viz_preview_present" -eq 1 ] \
    && [ "$viz_metadata_present" -eq 1 ] && [ "$viz_trajectory_sample_present" -eq 1 ]; then
    viz_state="included"
elif [ "$viz_animation_present" -eq 1 ] || [ "$viz_preview_present" -eq 1 ] \
    || [ "$viz_metadata_present" -eq 1 ] || [ "$viz_trajectory_sample_present" -eq 1 ]; then
    viz_state="partially_included"
else
    viz_state="absent"
fi

# Repository provenance. A reviewer reading only the archive otherwise has no
# way to tell which revision it came from, or whether the tree was dirty.
git_provenance_present=0
if git rev-parse --git-dir >/dev/null 2>&1; then
    git_provenance_present=1
    {
        printf '# Repository provenance\n\n'
        printf 'commit: %s\n' "$(git rev-parse HEAD)"
        printf 'branch: %s\n' "$(git rev-parse --abbrev-ref HEAD)"
        printf 'describe: %s\n' "$(git describe --always --dirty --tags 2>/dev/null || printf 'n/a')"
        printf 'worktree_clean: %s\n\n' "$([ -z "$(git status --porcelain)" ] && printf 'yes' || printf 'no')"
        printf '## Recent commits\n\n'
        git log --oneline -20 2>/dev/null || true
        printf '\n## Uncommitted changes at bundle time\n\n'
        if [ -n "$(git status --porcelain)" ]; then
            git status --porcelain
            printf '\nThe archive reflects the working tree, not the committed revision.\n'
        else
            printf 'none\n'
        fi
    } > "$bundle_root/GIT_PROVENANCE.md"
    record_manifest_row "GIT_PROVENANCE.md" "repository-provenance"
fi

cat > "$bundle_root/SECTION_STATUS.tsv" <<EOF
section	source_path	state	note
source	src/	$([ "$src_present" -eq 1 ] && printf 'included' || printf 'absent')	Source code is included when the directory exists.
documentation	docs/	included	Repository documentation is included.
context	context/	included	Scientific context and user-provided specifications are included.
models	models/	$([ "$models_present" -eq 1 ] && printf 'executable_model_present' || printf 'templates_only')	Model documentation is included; executable BND/CFG files are reported separately.
results	output/results/	$([ "$results_present" -eq 1 ] && printf 'included_if_eligible' || printf 'absent')	Eligible result files are included when present.
smoke_run	${latest_smoke_run:-output/smoke/}	$([ -n "$latest_smoke_run" ] && printf 'included' || printf 'absent')	Exactly one smoke run is bundled. The source_path column records which one, so a reviewer never has to infer it. Selected by $([ -n "$smoke_run_override" ] && printf '--smoke-run' || printf 'newest run_manifest.json mtime').
protein_readouts	data/proteinas secretadas ADOC.xlsx	$([ "$protein_readout_present" -eq 1 ] && printf 'included_with_full_tsv_exports' || printf 'absent')	The small source workbook is explicitly allowlisted and exported without value transformation.
visualization	docs/assets/adoc_maboss_pathway_dynamics.*	$viz_state	Pathway-dynamics animation, static preview, run metadata, and one node-probability-trajectory sample; each is reported individually in the manifest.
harness	AGENTS.md and docs/codex/	$([ "$include_harness" -eq 1 ] && printf 'included' || printf 'omitted_by_flag')	Agent definitions, skills, harness docs, and the harness validator.
visualization_runs	output/visualization/	$([ -d output/visualization ] && printf 'included_without_full_resolution_gif' || printf 'absent')	Animation metadata and the raw node-probability trajectories it was drawn from.
git_provenance	.git	$([ "$git_provenance_present" -eq 1 ] && printf 'included' || printf 'absent')	Commit, branch, recent log, and whether the worktree was dirty.
papers	data/*.pdf and data/*.docx	excluded	Paper context is summarized in context/; full papers are not bundled.
rds	data/*.rds	excluded	RDS objects are always excluded.
other_source_data	data/	excluded	Raw source data are excluded; its documentation is docs/source_data.md, carried with the docs tree.
EOF
record_manifest_row "SECTION_STATUS.tsv" "bundle-section-status"

cat > "$bundle_root/CHATGPT_BUNDLE_README.md" <<'EOF'
# DT_ADOC ChatGPT review bundle

This archive contains repository source code, model files, documentation,
scientific context, configuration, tests, and eligible analysis results.

`SECTION_STATUS.tsv` records which optional sections existed when the archive
was created. `CHATGPT_BUNDLE_MANIFEST.tsv` records the size, SHA-256 digest, and
inclusion reason for every other bundled file.

The archive intentionally excludes RDS objects, full papers, other immutable
source data, caches, checkpoints, nested archives, and files larger than 20 MiB.
The small ADOC protein-readout workbook is an explicit exception: it is included
with complete per-sheet TSV exports, source hash, and sheet metadata. Absence of
a result section means that no eligible result was available; it does not imply
a successful or empty analysis.

Model outputs remain conditional simulation results. They are not clinical
probabilities, validated contraceptive targets, or treatment recommendations.

See `docs/visualization.md` and `docs/assets/adoc_maboss_pathway_dynamics.gif` for the
MaBoSS pathway-dynamics animation. Node values shown in the animation are P(node = ON)
across simulated MaBoSS trajectories, not concentrations.
EOF
if [ "$include_harness" -eq 1 ]; then
    printf '\nRepository-local Codex harness, agent, and skill files were included by request.\n' \
        >> "$bundle_root/CHATGPT_BUNDLE_README.md"
fi
record_manifest_row "CHATGPT_BUNDLE_README.md" "bundle-readme"

{
    printf 'path\tsize_bytes\tsha256\tinclusion_reason\n'
    sort -u "$manifest_rows"
} > "$bundle_root/CHATGPT_BUNDLE_MANIFEST.tsv"

tar -czf "$bundle" -C "$stage" DT_ADOC_chatgpt_bundle
size_bytes="$(stat -c '%s' "$bundle")"
if [ "$size_bytes" -gt "$max_bundle_bytes" ]; then
    printf 'Bundle is %.2f MiB, above the 60 MiB limit; removing generated archive.\n' \
        "$(awk -v bytes="$size_bytes" 'BEGIN {printf "%.2f", bytes / 1024 / 1024}')" >&2
    rm -f -- "$bundle"
    exit 1
fi

PYTHONDONTWRITEBYTECODE=1 python -B src/scripts/validate_chatgpt_bundle.py "$bundle"
printf 'Created %s (%.2f MiB)\n' "$bundle" \
    "$(awk -v bytes="$size_bytes" 'BEGIN {printf "%.2f", bytes / 1024 / 1024}')"
