"""Command-line entry point for a reproducible reactor run."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import ReactorConfig
from .reactor import simulate
from .reporting import write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the reduced M4 packed-bed reactor model.")
    parser.add_argument("--config", required=True, help="Path to a JSON reactor configuration.")
    parser.add_argument("--output", required=True, help="Directory for profiles, summary, and figures.")
    args = parser.parse_args()
    config = ReactorConfig.from_json(args.config)
    result = simulate(config)
    write_outputs(result, Path(args.output))
    print(f"status={'completed' if result.success else 'incomplete_or_failed'}")
    print(f"outlet_co_conversion={result.co_conversion[-1]:.6g}")
    print(f"peak_temperature_k={result.temperature_k.max():.6g}")
    print(f"outputs={Path(args.output).resolve()}")
    if not result.success:
        raise SystemExit(result.message)


if __name__ == "__main__":
    main()
