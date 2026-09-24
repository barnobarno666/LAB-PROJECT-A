"""Isolated Full-M4 sensitivity of CO conversion to inlet nitrogen flow."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .feed_flow_sensitivity import _axis_with_references, _common_model_config, _simulate_flows
from .plotting import apply_design3_style


def run_sweep(
    group14_data_path: Path,
    experiment1_data_path: Path,
    output_dir: Path,
    *,
    flow_points: int = 41,
    n2_min_mol_h: float = 0.4,
    n2_max_mol_h: float = 1.2,
    catalyst_mass_g: float = 3.12,
    pressure_bar: float = 1.0,
) -> dict[str, object]:
    """Vary N2 while holding CO, H2, catalyst, temperature, and model setup fixed."""
    if flow_points < 5:
        raise ValueError("flow_points must be at least 5.")
    if n2_min_mol_h <= 0.0 or n2_max_mol_h <= n2_min_mol_h:
        raise ValueError("N2 bounds must be positive and increasing.")

    group14 = json.loads(group14_data_path.read_text(encoding="utf-8"))
    experiment1 = json.loads(experiment1_data_path.read_text(encoding="utf-8"))
    flows = experiment1["inlet_molar_flow_mol_h"]
    fixed_co = float(flows["CO"])
    fixed_h2 = float(flows["H2"])
    reference_n2 = float(flows["N2"])
    n2_values = _axis_with_references(
        np.linspace(n2_min_mol_h, n2_max_mol_h, flow_points), (reference_n2,)
    )

    base_config = _common_model_config(
        group14,
        experiment1,
        catalyst_mass_g=catalyst_mass_g,
        pressure_bar=pressure_bar,
    )
    records: list[dict[str, object]] = []
    for index, n2_flow in enumerate(n2_values, start=1):
        conversion, success, message = _simulate_flows(
            base_config,
            {"CO": fixed_co, "H2": fixed_h2, "N2": float(n2_flow)},
        )
        records.append(
            {
                "n2_feed_mol_h": float(n2_flow),
                "co_feed_mol_h": fixed_co,
                "h2_feed_mol_h": fixed_h2,
                "total_feed_mol_h": fixed_co + fixed_h2 + float(n2_flow),
                "h2_co_molar_ratio": fixed_h2 / fixed_co,
                "co_conversion_pct": conversion if success else float("nan"),
                "status": "completed" if success else "incomplete",
                "solver_message": message,
            }
        )
        print(f"N2 sweep: solved {index}/{len(n2_values)} cases", flush=True)

    failed = sum(record["status"] != "completed" for record in records)
    if failed:
        raise RuntimeError(f"{failed} of {len(records)} nitrogen-flow cases did not complete.")

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "n2_conversion_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    conversion_values = np.array(
        [float(record["co_conversion_pct"]) for record in records], dtype=float
    )
    reference_index = int(np.argmin(np.abs(n2_values - reference_n2)))
    reference_conversion = float(conversion_values[reference_index])

    apply_design3_style(font_size=13)
    fig, ax = plt.subplots(figsize=(7.6, 5.3), facecolor="#fffdf9")
    ax.set_facecolor("#fffdf9")
    ax.plot(
        n2_values,
        conversion_values,
        color="#0F2537",
        linewidth=2.0,
        marker="o",
        markersize=4.2,
        markerfacecolor="#fffdf9",
        markeredgecolor="#0077B6",
        markeredgewidth=1.25,
        label="Full M4 model",
    )
    ax.axvline(reference_n2, color="#C92A2A", linestyle=(0, (2, 2)), linewidth=1.1)
    ax.scatter(
        [reference_n2],
        [reference_conversion],
        marker="s",
        s=58,
        facecolor="#fffdf9",
        edgecolor="#C92A2A",
        linewidth=1.6,
        zorder=4,
        label="Experiment 1 inlet N$_2$",
    )
    ax.annotate(
        f"Reference: {reference_conversion:.2f}% at {reference_n2:.3f} mol/h",
        xy=(reference_n2, reference_conversion),
        xytext=(8, 12),
        textcoords="offset points",
        color="#C92A2A",
        fontsize=9.5,
    )
    ax.set_xlabel(r"Inlet N$_2$ flow, $F_{\mathrm{N_2,in}}$ (mol h$^{-1}$)")
    ax.set_ylabel("Outlet CO conversion (%)")
    ax.set_xlim(n2_min_mol_h, n2_max_mol_h)
    ax.set_ylim(0.0, 100.0)
    ax.set_yticks(np.arange(0.0, 101.0, 20.0))
    ax.grid(axis="y", color="#EAEAEA", linewidth=0.8)
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout(pad=0.8)
    for suffix in ("png", "svg"):
        figure_path = output_dir / f"n2_conversion_sweep.{suffix}"
        fig.savefig(figure_path, dpi=600, bbox_inches="tight")
        if suffix == "svg":
            lines = figure_path.read_text(encoding="utf-8").splitlines()
            figure_path.write_text(
                "\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8"
            )
    plt.close(fig)

    metadata: dict[str, object] = {
        "model": "m4_full",
        "metric": "completed-bed outlet CO conversion percent",
        "sweep": {
            "varied": "N2 inlet molar flow",
            "n2_range_mol_h": [float(n2_values[0]), float(n2_values[-1])],
            "number_of_cases": len(records),
            "reference_n2_mol_h": reference_n2,
            "reference_conversion_pct": reference_conversion,
        },
        "fixed_inputs": {
            "co_inlet_mol_h": fixed_co,
            "h2_inlet_mol_h": fixed_h2,
            "h2_co_molar_ratio": fixed_h2 / fixed_co,
            "inlet_temperature_c": float(experiment1["basis"]["reaction_temperature_c"]),
            "inlet_pressure_bar_abs": pressure_bar,
            "catalyst_mass_g": catalyst_mass_g,
            "thermal_mode": "isothermal",
            "transport_mode": "constant_pressure",
            "solver_method": "BDF",
            "solver_rtol": 1.0e-6,
            "solver_atol_flow_mol_s": 1.0e-10,
        },
        "interpretation": [
            "CO and H2 inlet molar flows are fixed while N2 flow changes.",
            "Changing N2 also changes total inlet flow and dilution; the resulting curve is the combined N2-flow effect under the stated fixed inputs.",
            "This is a conditional no-fit model sensitivity, not experimental validation.",
            f"The {pressure_bar:g} bar predictions extrapolate below the model's 5-15 bar kinetic-fit pressure range.",
        ],
        "outputs": [csv_path.name, "n2_conversion_sweep.png", "n2_conversion_sweep.svg"],
    }
    (output_dir / "n2_sweep_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        f"""# Isolated nitrogen-flow sensitivity

Run from the project root with:

```powershell
uv run m4-sweep-n2-flow
```

The no-fit Full M4 model holds CO at {fixed_co:.3f} mol/h and H2 at {fixed_h2:.3f} mol/h, then varies N2 from {n2_values[0]:.3f} to {n2_values[-1]:.3f} mol/h. The reference feed contains {reference_n2:.3f} mol/h N2. Temperature is {float(experiment1['basis']['reaction_temperature_c']):g} °C, pressure is {pressure_bar:g} bar absolute, catalyst mass is {catalyst_mass_g:g} g, and operation is isothermal with constant pressure along the bed.

Because CO and H2 stay fixed, increasing N2 also increases total feed and dilutes the reactive species. The result isolates N2 as the changed input, while showing its combined dilution and throughput effects. At {pressure_bar:g} bar, the model is extrapolated below its 5-15 bar kinetic-fit range. Treat the curve as a conditional model sensitivity, not experimental validation.

`n2_conversion_sweep.csv` contains the individual cases and solver status; `n2_sweep_metadata.json` records inputs and caveats.
""",
        encoding="utf-8",
    )
    print(
        f"completed={len(records)} conversion_pct={conversion_values.min():.3f}.."
        f"{conversion_values.max():.3f} reference_pct={reference_conversion:.3f}"
    )
    print(f"outputs={output_dir.resolve()}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Isolate the Full-M4 conversion response to N2 inlet flow."
    )
    parser.add_argument("--group14-data", type=Path, default=Path("data/group14_observed_data.json"))
    parser.add_argument(
        "--experiment1-data", type=Path, default=Path("data/experiment1_observed_data.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/experiment1_n2_isolated_sensitivity_1bar")
    )
    parser.add_argument("--flow-points", type=int, default=41)
    parser.add_argument("--n2-min-mol-h", type=float, default=0.4)
    parser.add_argument("--n2-max-mol-h", type=float, default=1.2)
    parser.add_argument("--catalyst-mass-g", type=float, default=3.12)
    parser.add_argument("--pressure-bar", type=float, default=1.0)
    args = parser.parse_args()
    run_sweep(
        args.group14_data,
        args.experiment1_data,
        args.output,
        flow_points=args.flow_points,
        n2_min_mol_h=args.n2_min_mol_h,
        n2_max_mol_h=args.n2_max_mol_h,
        catalyst_mass_g=args.catalyst_mass_g,
        pressure_bar=args.pressure_bar,
    )


if __name__ == "__main__":
    main()
