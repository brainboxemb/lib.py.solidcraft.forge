"""Feature identity, configuration and model semantic IR.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core import Shape
from .base import ParameterIR
from .body import IRNode

class FeatureRefIR:
    """Engine-neutral semantic reference to one normalized authored feature."""

    path: tuple[str, ...]

    def __post_init__(self):
        if (
            not isinstance(self.path, tuple)
            or not self.path
            or any(
                not isinstance(segment, str)
                or not segment
                or not segment.replace("_", "").isalnum()
                for segment in self.path
            )
        ):
            raise ValueError(
                "FeatureRefIR path must contain semantic non-empty path segments"
            )


@dataclass(frozen=True)
class NamedFeatureIR:
    """Public semantic name/state for one exact authored history feature."""

    name: str
    feature: FeatureRefIR
    suppressed: bool = False

    def __post_init__(self):
        if (
            not isinstance(self.name, str)
            or not self.name.isidentifier()
            or self.name.startswith("_")
        ):
            raise ValueError("NamedFeatureIR name must be public identity")
        if not isinstance(self.feature, FeatureRefIR):
            raise ValueError("NamedFeatureIR feature must be FeatureRefIR")
        if not isinstance(self.suppressed, bool):
            raise ValueError("NamedFeatureIR suppressed must be bool")


@dataclass(frozen=True)
class ParameterColumnIR:
    """One configured public parameter column."""

    name: str

    def __post_init__(self):
        if (
            not isinstance(self.name, str)
            or not self.name.isidentifier()
        ):
            raise ValueError(
                "ParameterColumnIR name must be a parameter identifier"
            )


@dataclass(frozen=True)
class SuppressionColumnIR:
    """One configuration column that suppresses exact semantic feature identity."""

    feature: Any

    def __post_init__(self):
        from ..assembly_ir import ComponentFeatureRefIR

        if not isinstance(
            self.feature,
            (
                FeatureRefIR,
                ComponentFeatureRefIR,
            ),
        ):
            raise ValueError(
                "SuppressionColumnIR feature must be semantic feature reference"
            )


@dataclass(frozen=True)
class ParameterCellIR:
    """One authored configuration-row expression/value for a parameter column."""

    expression: str

    def __post_init__(self):
        if (
            not isinstance(self.expression, str)
            or not self.expression.strip()
        ):
            raise ValueError(
                "ParameterCellIR expression must be non-empty authored text"
            )


ConfigurationColumnIR = ParameterColumnIR | SuppressionColumnIR
ConfigurationCellIR = ParameterCellIR | bool


@dataclass(frozen=True)
class ConfigurationRowIR:
    """One named row of heterogeneous typed configuration cells."""

    name: str
    cells: tuple[ConfigurationCellIR, ...]

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("ConfigurationRowIR name must be non-empty text")
        if not isinstance(self.cells, tuple):
            raise ValueError("ConfigurationRowIR cells must be tuple")
        if any(
            not isinstance(cell, (ParameterCellIR, bool))
            for cell in self.cells
        ):
            raise ValueError(
                "ConfigurationRowIR cells must be parameter expressions or bool"
            )


@dataclass(frozen=True)
class ConfigurationIR:
    """Current public final-model configuration table semantics."""

    active: str
    columns: tuple[ConfigurationColumnIR, ...]
    rows: tuple[ConfigurationRowIR, ...]

    def __post_init__(self):
        if (
            not isinstance(self.columns, tuple)
            or not self.columns
            or any(
                not isinstance(
                    column,
                    (ParameterColumnIR, SuppressionColumnIR),
                )
                for column in self.columns
            )
        ):
            raise ValueError(
                "ConfigurationIR requires parameter or suppression columns"
            )
        if (
            not isinstance(self.rows, tuple)
            or not self.rows
            or any(not isinstance(row, ConfigurationRowIR) for row in self.rows)
        ):
            raise ValueError("ConfigurationIR requires named rows")
        if len({row.name for row in self.rows}) != len(self.rows):
            raise ValueError("ConfigurationIR row names must be unique")
        if self.active not in {row.name for row in self.rows}:
            raise ValueError(
                "ConfigurationIR active row must name a declared row"
            )
        if any(len(row.cells) != len(self.columns) for row in self.rows):
            raise ValueError(
                "ConfigurationIR row cell count must match column count"
            )
        for row in self.rows:
            for column, cell in zip(self.columns, row.cells):
                if (
                    isinstance(column, ParameterColumnIR)
                    and not isinstance(cell, ParameterCellIR)
                ):
                    raise ValueError(
                        "parameter configuration columns require ParameterCellIR"
                    )
                if (
                    isinstance(column, SuppressionColumnIR)
                    and not isinstance(cell, bool)
                ):
                    raise ValueError(
                        "suppression configuration columns require bool cells"
                    )




@dataclass(frozen=True)
class ModelIR:
    """One normalized Forge model independent of a native CAD backend."""

    root: IRNode
    parameters: tuple[ParameterIR, ...]
    configuration: ConfigurationIR | None = None
    named_features: tuple[NamedFeatureIR, ...] = ()

    def __post_init__(self):
        if (
            self.configuration is not None
            and not isinstance(self.configuration, ConfigurationIR)
        ):
            raise ValueError(
                "ModelIR configuration must be ConfigurationIR or None"
            )
        if (
            not isinstance(self.named_features, tuple)
            or any(
                not isinstance(feature, NamedFeatureIR)
                for feature in self.named_features
            )
        ):
            raise ValueError("ModelIR named_features must be NamedFeatureIR")
        names = [feature.name for feature in self.named_features]
        if len(set(names)) != len(names):
            raise ValueError("ModelIR named feature names must be unique")


@dataclass(frozen=True)
class ConfiguredDesignIR:
    """Configuration intent around one semantic Shape model or Assembly."""

    design: Any
    configuration: ConfigurationIR

    def __post_init__(self):
        from ..assembly_ir import AssemblyIR

        if not isinstance(self.design, (ModelIR, AssemblyIR)):
            raise ValueError(
                "ConfiguredDesignIR design must be ModelIR or AssemblyIR"
            )
        if not isinstance(self.configuration, ConfigurationIR):
            raise ValueError(
                "ConfiguredDesignIR configuration must be ConfigurationIR"
            )
