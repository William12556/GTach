"""
AEL Context Budget Calculator.

Standalone script — no model connection or task required.
Reads config.yaml and the model's config.json from disk, computes
context budget numbers, and writes context-budget.md to the state
directory for Strategic Domain consumption.

Run this once after project setup and after any model change.

Usage:
    python ai/ael/src/budget.py
    python ai/ael/src/budget.py --config ai/ael/config.yaml
"""

import argparse
import datetime
import glob
import json
import os
import sys

import yaml


def load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def resolve_context_window(model_name: str, models_dir: str, override: int | None) -> tuple[int | None, str]:
    """
    Resolve context window in tokens.
    Returns (context_window, source_description).
    """
    if override is not None:
        return override, "config.yaml override"

    if not models_dir:
        return None, "models_dir not configured"

    pattern = os.path.join(models_dir, "**", model_name, "config.json")
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        return None, f"config.json not found under {models_dir}/{model_name}"

    cfg_path = matches[0]
    try:
        with open(cfg_path) as f:
            cfg = json.load(f)
        ctx = (
            cfg.get("max_position_embeddings")
            or (cfg.get("text_config") or {}).get("max_position_embeddings")
        )
        if ctx:
            return int(ctx), cfg_path
        return None, f"max_position_embeddings not found in {cfg_path}"
    except Exception as exc:
        return None, f"failed to read {cfg_path}: {exc}"


def write_report(
    state_dir: str,
    model: str,
    context_window: int | None,
    source: str,
    warn_pct: float,
    abort_pct: float,
) -> str:
    """Write context-budget.md and return the output path."""
    os.makedirs(state_dir, exist_ok=True)
    out_path = os.path.join(state_dir, "context-budget.md")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if context_window is None:
        report = (
            f"# AEL Context Budget Report\n\n"
            f"Generated: {now}\n"
            f"Model: {model}\n"
            f"Source: {source}\n\n"
            f"Context window could not be determined.\n"
            f"Set `context.context_window` in config.yaml to enable budget tracking.\n"
            f"Or ensure `context.models_dir` points to your local model storage.\n"
        )
        with open(out_path, "w") as f:
            f.write(report)
        return out_path

    warn_tokens  = int(context_window * warn_pct)
    abort_tokens = int(context_window * abort_pct)
    est_per_iter = 300
    # Recommended brief: ~400 tokens task + ~300 token system prompt overhead
    recommended_max_brief = 1000
    brief_pct = (recommended_max_brief / context_window) * 100
    iters_to_warn  = max(0, (warn_tokens  - recommended_max_brief) // est_per_iter)
    iters_to_abort = max(0, (abort_tokens - recommended_max_brief) // est_per_iter)

    report = f"""# AEL Context Budget Report

Generated: {now}
Model: {model}
Source: {source}
Context window: {context_window:,} tokens

## Budget thresholds
Warn at:  {warn_tokens:,} tokens ({warn_pct*100:.0f}%)
Abort at: {abort_tokens:,} tokens ({abort_pct*100:.0f}%)

## Task sizing guidance
Recommended maximum tactical_brief size: {recommended_max_brief:,} tokens ({brief_pct:.1f}% of window)
Estimated accumulation per phase iteration: ~{est_per_iter} tokens

At recommended brief size:
  Iterations before warn threshold:  ~{iters_to_warn}
  Iterations before abort threshold: ~{iters_to_abort}

## Guidance for Strategic Domain
When authoring a tactical_brief or T04 prompt:

- Keep tactical_brief to ≤{recommended_max_brief:,} tokens (~{recommended_max_brief * 4:,} characters)
- Brief should contain only: file(s) to modify, constraints, steps, deliverables, success criteria
- Do not embed design documents, code blocks, or YAML schemas in the brief
- Context pressure symptoms: duplicate tool calls, repeated reads, verbose looping responses
- If symptoms appear, reduce brief size and run --mode reset before retrying

Token estimation: 1 token ≈ 4 characters (Mistral BPE approximation, slight overestimate)
"""
    with open(out_path, "w") as f:
        f.write(report)
    return out_path


def main() -> None:
    default_config = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    p = argparse.ArgumentParser(description="AEL Context Budget Calculator")
    p.add_argument("--config", default=default_config, help="Path to config.yaml")
    args = p.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: config not found: {args.config}")
        sys.exit(1)

    config    = load_yaml(args.config)
    omlx_cfg  = config["omlx"]
    model     = omlx_cfg["default_model"]
    state_dir = os.path.abspath(config["loop"]["state_dir"])
    ctx_cfg   = config.get("context", {})
    models_dir  = ctx_cfg.get("models_dir", "")
    budget_warn  = ctx_cfg.get("budget_warn_pct", 0.80)
    budget_abort = ctx_cfg.get("budget_abort_pct", 0.95)

    context_window, source = resolve_context_window(
        model, models_dir, ctx_cfg.get("context_window")
    )

    out_path = write_report(
        state_dir, model, context_window, source, budget_warn, budget_abort
    )

    if context_window:
        print(f"Model:          {model}")
        print(f"Context window: {context_window:,} tokens")
        print(f"Source:         {source}")
        print(f"Report written: {out_path}")
    else:
        print(f"Model:   {model}")
        print(f"Warning: context window not determined — {source}")
        print(f"Report written: {out_path}")


if __name__ == "__main__":
    main()
