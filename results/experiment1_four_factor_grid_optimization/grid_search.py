"""Four-factor, full-M4 grid search on the Experiment 1 plotting ranges."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from copy import deepcopy
from datetime import datetime, timezone
import itertools
import json
import math
import os
from pathlib import Path
import time

from methanation.config import ReactorConfig
from methanation.reactor import simulate
from methanation.stoich_temperature_pressure_sensitivity import _experiment1_config


_BASE_CONFIG: dict | None = None
_FIXED: dict[str, float] | None = None


def _worker_init(config_data: dict, fixed: dict[str, float]) -> None:
    global _BASE_CONFIG, _FIXED
    _BASE_CONFIG = config_data
    _FIXED = fixed


def _solve_batch(batch: list[tuple[int, float, float, float, float]]) -> list[dict[str, object]]:
    if _BASE_CONFIG is None or _FIXED is None:
        raise RuntimeError("Grid worker was not initialized.")
    rows: list[dict[str, object]] = []
    baseline_tau = _FIXED["space_time_kg_s_mol_co"]
    baseline_co = _FIXED["co_feed_mol_h"]
    n2_co_ratio = _FIXED["n2_co_ratio"]

    for case_id, ratio, temperature_c, pressure_bar, space_time in batch:
        multiple = space_time / baseline_tau
        co_mol_h = baseline_co / multiple
        h2_mol_h = ratio * co_mol_h
        n2_mol_h = n2_co_ratio * co_mol_h
        scenario = deepcopy(_BASE_CONFIG)
        scenario["feed"]["temperature_k"] = temperature_c + 273.15
        scenario["feed"]["pressure_bar"] = pressure_bar
        scenario["feed"]["total_molar_flow_mol_s"] = (
            co_mol_h + h2_mol_h + n2_mol_h
        ) / 3600.0
        scenario["feed"]["mole_ratio"] = {
            "CO": co_mol_h,
            "H2": h2_mol_h,
            "N2": n2_mol_h,
        }

        row: dict[str, object] = {
            "case_id": case_id,
            "h2_co_molar_ratio": ratio,
            "inlet_temperature_c": temperature_c,
            "inlet_pressure_bar_abs": pressure_bar,
            "catalyst_space_time_kg_s_mol_co": space_time,
            "space_time_multiple_of_experiment1": multiple,
            "co_feed_mol_h": co_mol_h,
            "h2_feed_mol_h": h2_mol_h,
            "n2_feed_mol_h": n2_mol_h,
            "total_feed_mol_h": co_mol_h + h2_mol_h + n2_mol_h,
        }
        try:
            result = simulate(ReactorConfig.from_dict(scenario))
            row.update(
                {
                    "outlet_co_conversion_pct": float(result.co_conversion[-1] * 100.0)
                    if result.success
                    else float("nan"),
                    "outlet_ch4_yield_pct": float(result.methane_yield[-1] * 100.0)
                    if result.success
                    else float("nan"),
                    "outlet_pressure_bar_abs": float(result.pressure_pa[-1] / 100000.0),
                    "pressure_drop_pa": float(result.pressure_pa[0] - result.pressure_pa[-1]),
                    "status": "completed" if result.success else "incomplete",
                    "terminal_event": result.terminal_event or "",
                    "solver_function_evaluations": int(result.nfev),
                    "message": result.message,
                }
            )
        except Exception as error:  # Keep every attempted grid point auditable.
            row.update(
                {
                    "outlet_co_conversion_pct": float("nan"),
                    "outlet_ch4_yield_pct": float("nan"),
                    "outlet_pressure_bar_abs": float("nan"),
                    "pressure_drop_pa": float("nan"),
                    "status": "error",
                    "terminal_event": "",
                    "solver_function_evaluations": 0,
                    "message": f"{type(error).__name__}: {error}",
                }
            )
        rows.append(row)
    return rows


def _load_axes(root: Path) -> tuple[list[float], list[float], list[float], list[float]]:
    three_factor_dir = root / "results/experiment1_stoich_temperature_pressure_sweep"
    two_factor_dir = root / "results/experiment1_ratio_contact_time_sweep"
    three_factor = json.loads((three_factor_dir / "sweep_metadata.json").read_text(encoding="utf-8"))
    ratios = [float(value) for value in three_factor["grid"]["h2_co_ratio"]]
    temperatures = [float(value) for value in three_factor["grid"]["inlet_temperature_c"]]
    pressures = [float(value) for value in three_factor["grid"]["inlet_pressure_bar_abs"]]
    with (two_factor_dir / "ratio_contact_time_sweep.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        space_times = sorted(
            {float(row["catalyst_space_time_kg_s_mol_co"]) for row in csv.DictReader(stream)}
        )
    return ratios, temperatures, pressures, space_times


def _chunked(values: list[tuple[int, float, float, float, float]], size: int):
    for start in range(0, len(values), size):
        yield values[start : start + size]


def run_search(root: Path, output: Path, workers: int) -> dict[str, object]:
    ratios, temperatures, pressures, space_times = _load_axes(root)
    base_config, fixed = _experiment1_config(
        root / "configs/assumed_base_case.json",
        root / "data/experiment1_observed_data.json",
        catalyst_mass_g=3.12,
        particle_density_kg_m3=1250.0,
    )
    config_data = base_config.to_dict()
    config_data["solver"]["method"] = "BDF"
    dimensions = (ratios, temperatures, pressures, space_times)
    points = [tuple(float(value) for value in point) for point in itertools.product(*dimensions)]
    cases = [(i, *point) for i, point in enumerate(points)]
    total = len(cases)
    batch_size = 96
    started = time.perf_counter()
    rows: list[dict[str, object]] = []
    completed_cases = 0

    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_worker_init,
        initargs=(config_data, fixed),
    ) as executor:
        futures = [executor.submit(_solve_batch, batch) for batch in _chunked(cases, batch_size)]
        for future in as_completed(futures):
            batch_rows = future.result()
            rows.extend(batch_rows)
            completed_cases += len(batch_rows)
            print(f"solved {completed_cases}/{total} cases", flush=True)

    rows.sort(key=lambda row: int(row["case_id"]))
    successful = [row for row in rows if row["status"] == "completed"]
    if not successful:
        raise RuntimeError("All grid-search model runs failed or ended before the bed outlet.")
    best = max(successful, key=lambda row: float(row["outlet_co_conversion_pct"]))

    reference_ratio = fixed["reference_h2_co_ratio"]
    reference_tau = fixed["space_time_kg_s_mol_co"]
    reference = next(
        row
        for row in successful
        if math.isclose(float(row["h2_co_molar_ratio"]), reference_ratio, abs_tol=1e-10)
        and math.isclose(float(row["inlet_temperature_c"]), fixed["reference_temperature_c"])
        and math.isclose(float(row["inlet_pressure_bar_abs"]), fixed["reference_pressure_bar_abs"])
        and math.isclose(float(row["catalyst_space_time_kg_s_mol_co"]), reference_tau, rel_tol=1e-10)
    )

    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "four_factor_grid_search.csv"
    fieldnames = list(rows[0])
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    best_axes = {
        "h2_co_molar_ratio": ratios,
        "inlet_temperature_c": temperatures,
        "inlet_pressure_bar_abs": pressures,
        "catalyst_space_time_kg_s_mol_co": space_times,
    }
    best_grid_position = {
        key: "lower bound" if math.isclose(float(best[key]), axis[0]) else
        "upper bound" if math.isclose(float(best[key]), axis[-1]) else "interior"
        for key, axis in best_axes.items()
    }
    metadata: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": "m4_full",
        "objective": "maximize completed-bed outlet CO conversion",
        "grid": {
            "h2_co_molar_ratio": ratios,
            "inlet_temperature_c": temperatures,
            "inlet_pressure_bar_abs": pressures,
            "catalyst_space_time_kg_s_mol_co": space_times,
            "point_count": total,
        },
        "completed_cases": len(successful),
        "failed_or_incomplete_cases": total - len(successful),
        "best_grid_case": {
            key: best[key]
            for key in (
                "h2_co_molar_ratio",
                "inlet_temperature_c",
                "inlet_pressure_bar_abs",
                "catalyst_space_time_kg_s_mol_co",
                "co_feed_mol_h",
                "h2_feed_mol_h",
                "n2_feed_mol_h",
                "outlet_co_conversion_pct",
                "outlet_ch4_yield_pct",
            )
        },
        "best_grid_position": best_grid_position,
        "reference_case": {
            "h2_co_molar_ratio": reference["h2_co_molar_ratio"],
            "inlet_temperature_c": reference["inlet_temperature_c"],
            "inlet_pressure_bar_abs": reference["inlet_pressure_bar_abs"],
            "catalyst_space_time_kg_s_mol_co": reference["catalyst_space_time_kg_s_mol_co"],
            "outlet_co_conversion_pct": reference["outlet_co_conversion_pct"],
            "source_reported_co_conversion_pct": fixed["source_reported_co_conversion_pct"],
        },
        "fixed_basis": {
            "catalyst_mass_g": fixed["catalyst_mass_g"],
            "n2_co_ratio": fixed["n2_co_ratio"],
            "bed_voidage": fixed["bed_voidage"],
            "particle_density_kg_m3_assumed": fixed["particle_density_kg_m3_assumed"],
            "thermal_mode": "isothermal",
            "transport_mode": "ergun",
            "solver_method": "BDF",
        },
        "kinetic_pressure_fit_domain_bar_abs": [5.0, 15.0],
        "interpretation": (
            "The reported maximum is the best sampled point in the combined grid, not a continuous optimum. "
            "The model maximizes CO conversion only; it imposes no penalty for H2 use, low throughput, "
            "or operating pressure. The Experiment 1 geometry and particle density are inherited assumptions, "
            "and the resulting bed voidage is sparse. The 1-4 bar points extrapolate the pressure-dependent kinetics. "
            "This is an exploratory model result, not experimental validation."
        ),
        "elapsed_seconds": time.perf_counter() - started,
        "outputs": [csv_path.name],
    }
    (output / "optimization_summary.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    (output / "README.md").write_text(
        "# Four-factor full-M4 grid search\n\n"
        "This exhaustive discrete grid combines the sampled values from the H2/CO-temperature-pressure "
        "map and the H2/CO-space-time contour. It maximizes model-predicted completed-bed outlet CO conversion.\n\n"
        f"The grid has {total:,} points; {len(successful):,} completed and "
        f"{total - len(successful):,} failed or incomplete. The best sampled case predicts "
        f"{float(best['outlet_co_conversion_pct']):.8f}% conversion at H2/CO="
        f"{float(best['h2_co_molar_ratio']):.8g}, {float(best['inlet_temperature_c']):.8g} °C, "
        f"{float(best['inlet_pressure_bar_abs']):.8g} bar abs, and "
        f"Wcat/FCO,in={float(best['catalyst_space_time_kg_s_mol_co']):.8g} kg_cat s/mol_CO.\n\n"
        "Catalyst mass (3.12 g), N2/CO ratio, assumed bed geometry, and voidage stay fixed. Space time is "
        "varied by scaling the CO, H2, and N2 feed rates together at each selected H2/CO ratio.\n\n"
        "The search maximizes conversion alone. It does not account for hydrogen consumption, throughput, "
        "or pressure cost. Pressures below 5 bar extrapolate the fitted pressure-dependent kinetics; the "
        "assumed 1 in × 12 in bed and particle density imply a sparse bed. Treat the result as an exploratory "
        "model optimum, not experimental validation. Full case data are in `four_factor_grid_search.csv`; "
        "the machine-readable summary is `optimization_summary.json`.\n",
        encoding="utf-8",
    )
    print(
        f"best_conversion_pct={float(best['outlet_co_conversion_pct']):.8f} "
        f"ratio={float(best['h2_co_molar_ratio']):.8g} "
        f"temperature_c={float(best['inlet_temperature_c']):.8g} "
        f"pressure_bar={float(best['inlet_pressure_bar_abs']):.8g} "
        f"space_time={float(best['catalyst_space_time_kg_s_mol_co']):.8g}"
    )
    print(f"reference_conversion_pct={float(reference['outlet_co_conversion_pct']):.8f}")
    print(f"completed={len(successful)}/{total}; failed_or_incomplete={total-len(successful)}")
    print(f"outputs={output.resolve()}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/experiment1_four_factor_grid_optimization"),
    )
    parser.add_argument("--workers", type=int, default=min(6, os.cpu_count() or 1))
    args = parser.parse_args()
    run_search(args.root.resolve(), args.output.resolve(), args.workers)


if __name__ == "__main__":
    main()
