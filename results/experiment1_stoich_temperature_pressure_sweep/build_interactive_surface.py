"""Build an offline-capable interactive Plotly view from the sweep CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import plotly.graph_objects as go


HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "stoich_temperature_pressure_sweep.csv"
METADATA_PATH = HERE / "sweep_metadata.json"
HTML_PATH = HERE / "stoich-temp-pressure.html"

COLORSCALE = [
    [0.00, "#24104f"],
    [0.20, "#63358d"],
    [0.40, "#bd4f91"],
    [0.60, "#ec865f"],
    [0.80, "#f5c96a"],
    [1.00, "#fff2c6"],
]
PAPER = "#fffdf9"
INK = "#241b35"


def _read_sweep() -> tuple[list[dict[str, object]], dict[str, object]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    failed = [row for row in rows if row["status"] != "completed"]
    if failed:
        raise ValueError(f"The sweep contains {len(failed)} incomplete cases; refusing to draw gaps as a surface.")
    return rows, metadata


def _make_figure(rows: list[dict[str, object]], metadata: dict[str, object]) -> go.Figure:
    fixed = metadata["fixed_basis"]
    ratios = sorted({float(row["h2_co_molar_ratio"]) for row in rows})
    temperatures = sorted({float(row["inlet_temperature_c"]) for row in rows})
    pressures = sorted({float(row["inlet_pressure_bar_abs"]) for row in rows})

    # The reference ratio (2.996875) and stoichiometric value (3.0) are nearly
    # identical. Keep the exact stoichiometric grid column and mark the actual
    # reference point separately to avoid a near-zero-width surface strip.
    reference_ratio = float(fixed["reference_h2_co_ratio"])
    surface_ratios = [
        ratio
        for ratio in ratios
        if abs(ratio - reference_ratio) > 1.0e-8
    ]
    records = {
        (
            round(float(row["h2_co_molar_ratio"]), 10),
            round(float(row["inlet_temperature_c"]), 8),
            round(float(row["inlet_pressure_bar_abs"]), 8),
        ): row
        for row in rows
    }

    fig = go.Figure()
    for pressure in pressures:
        conversion = [
            [
                float(
                    records[
                        (round(ratio, 10), round(temperature, 8), round(pressure, 8))
                    ]["outlet_co_conversion_pct"]
                )
                for ratio in surface_ratios
            ]
            for temperature in temperatures
        ]
        pressure_z = [[pressure] * len(surface_ratios) for _ in temperatures]
        fig.add_trace(
            go.Surface(
                x=surface_ratios,
                y=temperatures,
                z=pressure_z,
                surfacecolor=conversion,
                customdata=conversion,
                coloraxis="coloraxis",
                name=f"P = {pressure:g} bar",
                legendgroup=f"pressure-{pressure:g}",
                showlegend=True,
                showscale=False,
                opacity=0.58,
                connectgaps=False,
                hovertemplate=(
                    "H<sub>2</sub>/CO: %{x:.3f}<br>"
                    "Inlet temperature: %{y:.0f} °C<br>"
                    "Inlet pressure: %{z:.0f} bar abs<br>"
                    "CO conversion: %{customdata:.2f}%<extra></extra>"
                ),
            )
        )

    # A translucent vertical sheet marks H2/CO = 3 across T and P.
    stoich_x = [[3.0] * len(pressures) for _ in temperatures]
    stoich_y = [[temperature] * len(pressures) for temperature in temperatures]
    pressure_grid = [pressures[:] for _ in temperatures]
    fig.add_trace(
        go.Surface(
            x=stoich_x,
            y=stoich_y,
            z=pressure_grid,
            surfacecolor=[[0.5] * len(pressures) for _ in temperatures],
            colorscale=[[0, "#df9b28"], [1, "#df9b28"]],
            cmin=0,
            cmax=1,
            showscale=False,
            opacity=0.12,
            name="Stoichiometric H₂/CO = 3",
            showlegend=True,
            hoverinfo="skip",
        )
    )

    # A horizontal sheet marks the 5 bar lower limit of the kinetic-fit range.
    fit_z = [[5.0] * len(surface_ratios) for _ in temperatures]
    fig.add_trace(
        go.Surface(
            x=surface_ratios,
            y=temperatures,
            z=fit_z,
            surfacecolor=[[0.5] * len(surface_ratios) for _ in temperatures],
            colorscale=[[0, "#756980"], [1, "#756980"]],
            cmin=0,
            cmax=1,
            showscale=False,
            opacity=0.16,
            name="5 bar kinetic-fit boundary",
            showlegend=True,
            hoverinfo="skip",
        )
    )

    reference_pressure = float(fixed["reference_pressure_bar_abs"])
    reference_temperature = float(fixed["reference_temperature_c"])
    reference_row = next(
        row
        for row in rows
        if abs(float(row["h2_co_molar_ratio"]) - reference_ratio) < 1.0e-8
        and abs(float(row["inlet_temperature_c"]) - reference_temperature) < 1.0e-8
        and abs(float(row["inlet_pressure_bar_abs"]) - reference_pressure) < 1.0e-8
    )
    reference_conversion = float(reference_row["outlet_co_conversion_pct"])
    reported_conversion = float(fixed["source_reported_co_conversion_pct"])
    fig.add_trace(
        go.Scatter3d(
            x=[reference_ratio],
            y=[reference_temperature],
            z=[reference_pressure],
            mode="markers",
            name=f"Experiment 1 model reference ({reference_conversion:.1f}%)",
            marker={
                "symbol": "diamond",
                "size": 8,
                "color": PAPER,
                "line": {"color": INK, "width": 2},
            },
            customdata=[[reference_conversion, reported_conversion]],
            hovertemplate=(
                "Experiment 1 reference<br>"
                "H<sub>2</sub>/CO: %{x:.4f}<br>"
                "Temperature: %{y:.0f} °C<br>"
                "Pressure: %{z:.2f} bar abs<br>"
                "Model conversion: %{customdata[0]:.2f}%<br>"
                "Source-reported conversion: %{customdata[1]:.2f}% (not a fit target)<extra></extra>"
            ),
        )
    )

    n_traces = len(fig.data)
    focus_reference = [
        pressure == reference_pressure for pressure in pressures
    ] + [True, True, True]
    show_all = [True] * n_traces
    fig.update_layout(
        title={
            "text": (
                "CO conversion by feed ratio, inlet temperature, and pressure"
                "<br><sup>Fixed catalyst space time = "
                f"{float(fixed['space_time_kg_s_mol_co']):.2f} kg<sub>cat</sub> s mol<sup>−1</sup><sub>CO</sub>; "
                "isothermal full M4; pressures below 5 bar extrapolate the kinetic fit</sup>"
            ),
            "x": 0.015,
            "xanchor": "left",
        },
        coloraxis={
            "cmin": 0,
            "cmax": 100,
            "colorscale": COLORSCALE,
            "colorbar": {
                "title": {"text": "CO conversion (%)"},
                "x": 0.77,
                "len": 0.72,
                "thickness": 18,
            },
        },
        scene={
            "domain": {"x": [0.0, 0.72], "y": [0.0, 1.0]},
            "xaxis": {
                "title": "Inlet H₂/CO molar ratio",
                "range": [1, 5],
                "tickvals": [1, 2, 3, 4, 5],
                "gridcolor": "#d6d0dc",
                "backgroundcolor": PAPER,
                "zerolinecolor": "#9d94a7",
            },
            "yaxis": {
                "title": "Inlet temperature (°C)",
                "range": [250, 400],
                "tickvals": [250, 300, 350, 400],
                "gridcolor": "#d6d0dc",
                "backgroundcolor": PAPER,
                "zerolinecolor": "#9d94a7",
            },
            "zaxis": {
                "title": "Inlet pressure (bar abs)",
                "range": [1, 15],
                "tickvals": [1, 2, 5, 10, 15],
                "gridcolor": "#d6d0dc",
                "backgroundcolor": PAPER,
                "zerolinecolor": "#9d94a7",
            },
            "aspectmode": "manual",
            "aspectratio": {"x": 1.15, "y": 1.4, "z": 1.15},
            "camera": {"eye": {"x": 1.6, "y": -1.65, "z": 1.25}},
            "dragmode": "orbit",
        },
        legend={
            "title": {"text": "Pressure slices (click to toggle)"},
            "x": 0.83,
            "y": 0.97,
            "xanchor": "left",
            "yanchor": "top",
            "groupclick": "togglegroup",
            "font": {"size": 11},
        },
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.015,
                "y": 1.04,
                "buttons": [
                    {"label": "All pressure layers", "method": "restyle", "args": [{"visible": show_all}]},
                    {"label": "2 bar reference slice", "method": "restyle", "args": [{"visible": focus_reference}]},
                ],
            }
        ],
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        font={"family": "DejaVu Serif, Georgia, serif", "size": 13, "color": INK},
        margin={"l": 10, "r": 250, "t": 115, "b": 20},
        height=850,
        autosize=True,
        uirevision="stoich-temperature-pressure-v1",
        showlegend=True,
    )
    fig.add_annotation(
        text=(
            f"Model reference: {reference_conversion:.2f}% · source-reported: {reported_conversion:.2f}% (not fitted)"
            " · surfaces interpolate between sampled grid points"
        ),
        xref="paper",
        yref="paper",
        x=0.015,
        y=-0.03,
        showarrow=False,
        xanchor="left",
        font={"size": 11, "color": "#51475e"},
    )
    return fig


def main() -> None:
    rows, metadata = _read_sweep()
    figure = _make_figure(rows, metadata)
    html = figure.to_html(
        include_plotlyjs=True,
        full_html=True,
        config={"responsive": True, "displaylogo": False, "scrollZoom": True},
        div_id="stoich-temp-pressure-plot",
    )
    html = html.replace(
        "<head>",
        "<head>\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        '<meta name="description" content="Interactive CO conversion map across inlet H2/CO ratio, temperature, and pressure." />\n'
        "<title>Interactive CO Conversion Map</title>",
        1,
    )
    html = "\n".join(line.rstrip() for line in html.splitlines()).rstrip() + "\n"
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote self-contained interactive plot: {HTML_PATH}")
    print(f"Size: {HTML_PATH.stat().st_size / (1024 * 1024):.2f} MiB")


if __name__ == "__main__":
    main()
