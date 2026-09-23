"""Configuration loading and validation for a single reactor run."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Any

import numpy as np

from .constants import INDEX, PA_PER_BAR, SPECIES


@dataclass(frozen=True)
class FeedConfig:
    total_molar_flow_mol_s: float
    mole_ratio: dict[str, float]
    temperature_k: float
    pressure_bar: float


@dataclass(frozen=True)
class BedConfig:
    tube_diameter_m: float
    bed_length_m: float
    catalyst_loading_kg_m3_bed: float
    void_fraction: float
    particle_diameter_m: float


@dataclass(frozen=True)
class ThermalConfig:
    mode: str
    wall_temperature_k: float
    overall_heat_transfer_w_m2_k: float


@dataclass(frozen=True)
class TransportConfig:
    mode: str
    gas_viscosity_pa_s: float


@dataclass(frozen=True)
class SolverConfig:
    method: str
    rtol: float
    atol_flow_mol_s: float
    atol_temperature_k: float
    atol_pressure_pa: float
    max_temperature_k: float
    min_pressure_pa: float
    min_hydrogen_partial_pressure_bar: float
    output_points: int


@dataclass(frozen=True)
class ReactorConfig:
    reaction_mode: str
    feed: FeedConfig
    bed: BedConfig
    thermal: ThermalConfig
    transport: TransportConfig
    activity: float
    solver: SolverConfig

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReactorConfig":
        config = cls(
            reaction_mode=str(data["reaction_mode"]),
            feed=FeedConfig(**data["feed"]),
            bed=BedConfig(**data["bed"]),
            thermal=ThermalConfig(**data["thermal"]),
            transport=TransportConfig(**data["transport"]),
            activity=float(data["activity"]),
            solver=SolverConfig(**data["solver"]),
        )
        config.validate()
        return config

    @classmethod
    def from_json(cls, path: str | Path) -> "ReactorConfig":
        with Path(path).open(encoding="utf-8") as stream:
            return cls.from_dict(json.load(stream))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def cross_section_m2(self) -> float:
        return float(np.pi * self.bed.tube_diameter_m**2 / 4.0)

    @property
    def bed_volume_m3(self) -> float:
        return self.cross_section_m2 * self.bed.bed_length_m

    @property
    def catalyst_mass_kg(self) -> float:
        return self.bed.catalyst_loading_kg_m3_bed * self.bed_volume_m3

    @property
    def inlet_flows_mol_s(self) -> np.ndarray:
        ratio = self.feed.mole_ratio
        total_ratio = sum(ratio.get(species, 0.0) for species in SPECIES)
        values = np.zeros(len(SPECIES), dtype=float)
        for species, value in ratio.items():
            if species not in INDEX:
                raise ValueError(f"Unknown feed species: {species}")
            values[INDEX[species]] = self.feed.total_molar_flow_mol_s * value / total_ratio
        return values

    @property
    def inlet_pressure_pa(self) -> float:
        return self.feed.pressure_bar * PA_PER_BAR

    def validate(self) -> None:
        if self.reaction_mode != "m4_reduced_co_wgs":
            raise ValueError("Only reaction_mode='m4_reduced_co_wgs' is implemented.")
        if self.thermal.mode not in {"isothermal", "adiabatic", "heat_exchange"}:
            raise ValueError("thermal.mode must be isothermal, adiabatic, or heat_exchange")
        if self.transport.mode not in {"constant_pressure", "ergun"}:
            raise ValueError("transport.mode must be constant_pressure or ergun")
        if self.solver.method not in {"Radau", "BDF"}:
            raise ValueError("solver.method must be Radau or BDF")
        positive = {
            "total_molar_flow_mol_s": self.feed.total_molar_flow_mol_s,
            "temperature_k": self.feed.temperature_k,
            "pressure_bar": self.feed.pressure_bar,
            "tube_diameter_m": self.bed.tube_diameter_m,
            "bed_length_m": self.bed.bed_length_m,
            "catalyst_loading_kg_m3_bed": self.bed.catalyst_loading_kg_m3_bed,
            "particle_diameter_m": self.bed.particle_diameter_m,
            "gas_viscosity_pa_s": self.transport.gas_viscosity_pa_s,
            "rtol": self.solver.rtol,
            "atol_flow_mol_s": self.solver.atol_flow_mol_s,
            "atol_temperature_k": self.solver.atol_temperature_k,
            "atol_pressure_pa": self.solver.atol_pressure_pa,
            "max_temperature_k": self.solver.max_temperature_k,
            "min_pressure_pa": self.solver.min_pressure_pa,
            "min_hydrogen_partial_pressure_bar": self.solver.min_hydrogen_partial_pressure_bar,
        }
        invalid = [name for name, value in positive.items() if value <= 0.0]
        if invalid:
            raise ValueError(f"These values must be positive: {', '.join(invalid)}")
        if not 0.0 < self.bed.void_fraction < 1.0:
            raise ValueError("bed.void_fraction must lie strictly between zero and one")
        if self.solver.output_points < 3:
            raise ValueError("solver.output_points must be at least 3")
        if self.thermal.overall_heat_transfer_w_m2_k < 0.0:
            raise ValueError("overall_heat_transfer_w_m2_k cannot be negative")
        if self.activity < 0.0:
            raise ValueError("activity cannot be negative")
        if self.thermal.wall_temperature_k <= 0.0:
            raise ValueError("wall_temperature_k must be positive")
        if any(value < 0.0 for value in self.feed.mole_ratio.values()):
            raise ValueError("feed mole ratios cannot be negative")
        if sum(self.feed.mole_ratio.values()) <= 0.0:
            raise ValueError("feed mole ratios must have a positive total")
        if self.feed.mole_ratio.get("H2", 0.0) <= 0.0:
            raise ValueError("The reduced M4 rate law requires positive inlet hydrogen.")
