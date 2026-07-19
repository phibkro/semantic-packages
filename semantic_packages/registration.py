"""Read-only inspection of manifest-governed package registration.

Shared mechanics inventory one exact union of manifest-selected theory and
package sources. The Stack actor wrapper pins its product authority and accepts
no override. Neither path executes adapters, campaigns, proof tooling, or
resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from semantic_packages import _finite_source, graph
from scripts import record_check


Address = tuple[str, str, str]


@dataclass(frozen=True)
class RegistrationRecord:
    """One schema-valid record observed in the theory/package union."""

    address: Address
    path: str
    sha256: str
    role: str


@dataclass(frozen=True)
class RegistrationObservation:
    """Deterministic inventory and diagnostics for a registration attempt."""

    package: str
    records: tuple[RegistrationRecord, ...]
    diagnostics: tuple[record_check.Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return not self.diagnostics


_MANIFEST = graph.inspect_manifest_authority(graph.DEFAULT_STACK_MANIFEST)
_THEORY_ROLES = frozenset({"theory-authored", "dependency"})
_PACKAGE_ROLES = frozenset({"package-authored"})


def _root_label(path: str) -> str:
    return path.split("/", 1)[0]


def _role_for_record(
    path: str, address: Address, role_by_address: dict[Address, str]
) -> str:
    # Ownership role is decided by accepted address identity, not by the
    # physical root a record happens to be observed under: an exact theory
    # or package address keeps its authored role even when moved to the
    # other root, since the physical root only governs registration validity
    # (see _registration_diagnostics), never who authored the content.
    governed_role = role_by_address.get(address)
    if governed_role is not None:
        return governed_role
    # Wholly unexpected address: no accepted identity exists to attribute
    # authorship to, so fall back to a deterministic root-derived label.
    # This observation is invalid regardless (REGISTRATION_UNEXPECTED_ADDRESS).
    return "package-authored" if _root_label(path) == "package" else "theory-authored"


def _address_text(address: Address) -> str:
    return record_check.fmt_tuple(dict(zip(("kind", "id", "version"), address)))


def _inventory(
    records: tuple[_finite_source._SourceRecord, ...],
    role_by_address: dict[Address, str],
) -> tuple[RegistrationRecord, ...]:
    inventory = [
        RegistrationRecord(
            address=record.address,
            path=record.path,
            sha256=record.sha256,
            role=_role_for_record(record.path, record.address, role_by_address),
        )
        for record in records
    ]
    return tuple(
        sorted(inventory, key=lambda item: (item.address, item.path, item.sha256, item.role))
    )


def _root_approved(
    root: str,
    theory_approved: dict[Address, str],
    package_approved: dict[Address, str],
) -> dict[Address, str]:
    if root == "theory":
        return theory_approved
    if root == "package":
        return package_approved
    return {}


def _registration_diagnostics(
    inventory: tuple[RegistrationRecord, ...],
    theory_approved: dict[Address, str],
    package_approved: dict[Address, str],
    product: str,
) -> list[record_check.Diagnostic]:
    diagnostics: list[record_check.Diagnostic] = []

    # Missing addresses are decided per-root: a theory address is only
    # satisfied by a record actually observed under the theory root, and a
    # package address only by a record observed under the package root.  An
    # address moved across roots is missing from its owning root even though
    # its bytes survive elsewhere.
    for root, approved in (("theory", theory_approved), ("package", package_approved)):
        observed_in_root = {
            item.address for item in inventory if _root_label(item.path) == root
        }
        for address in sorted(set(approved) - observed_in_root):
            diagnostics.append(
                record_check.Diagnostic(
                    "REGISTRATION_MISSING_ADDRESS",
                    ".",
                    "#",
                    f"{product} package registration requires {_address_text(address)}",
                )
            )

    for item in inventory:
        approved = _root_approved(_root_label(item.path), theory_approved, package_approved)
        expected_sha256 = approved.get(item.address)
        if expected_sha256 is None:
            diagnostics.append(
                record_check.Diagnostic(
                    "REGISTRATION_UNEXPECTED_ADDRESS",
                    item.path,
                    "#",
                    f"{product} package registration does not include "
                    f"{_address_text(item.address)}",
                )
            )
        elif item.sha256 != expected_sha256:
            diagnostics.append(
                record_check.Diagnostic(
                    "REGISTRATION_SOURCE_DIGEST_MISMATCH",
                    item.path,
                    "#",
                    f"record {_address_text(item.address)} has SHA-256 {item.sha256}, "
                    f"expected {expected_sha256}",
                )
            )
    return diagnostics


def _selector_observation(
    package: str, code: str, message: str
) -> RegistrationObservation:
    return RegistrationObservation(
        package, (), (record_check.Diagnostic(code, ".", "#", message),)
    )


def inspect_package_registration(
    theory_root: Path,
    package_root: Path,
    package: str,
    *,
    authority: graph.ManifestAuthority,
    theory_source: str,
    product: str,
) -> RegistrationObservation:
    """Observe an exact theory/package union under supplied authority."""

    if not authority.ok:
        return RegistrationObservation(package, (), authority.diagnostics)

    sources = {item.source_id: item for item in authority.sources}
    declared_theory = sources.get(theory_source)
    if declared_theory is None:
        return _selector_observation(
            package,
            "REGISTRATION_UNKNOWN_THEORY_SOURCE",
            f"no {product} theory source selector for {theory_source!r}",
        )
    if not declared_theory.roles.issubset(_THEORY_ROLES):
        return _selector_observation(
            package,
            "REGISTRATION_THEORY_SOURCE_ROLE_MISMATCH",
            f"{product} theory source {theory_source!r} does not permit only "
            "theory-authored/dependency roles",
        )

    declared_package = sources.get(package)
    if declared_package is None:
        return _selector_observation(
            package,
            "REGISTRATION_UNKNOWN_PACKAGE_SOURCE",
            f"no {product} package source selector for {package!r}",
        )
    if not declared_package.roles.issubset(_PACKAGE_ROLES):
        return _selector_observation(
            package,
            "REGISTRATION_PACKAGE_SOURCE_ROLE_MISMATCH",
            f"{product} package source {package!r} does not permit only "
            "package-authored roles",
        )

    theory_approved = {
        member.address: member.sha256
        for member in authority.members
        if member.source == theory_source
    }
    package_approved = {
        member.address: member.sha256
        for member in authority.members
        if member.source == package
    }
    role_by_address = {
        member.address: member.role for member in authority.members
    }

    source = _finite_source._observe_finite_source(
        (
            _finite_source._SourceRoot("theory", theory_root),
            _finite_source._SourceRoot("package", package_root),
        )
    )
    diagnostics = list(source.diagnostics)
    inventory = _inventory(source.records, role_by_address)

    # Preserve the loader's input/schema phase barrier.  Graph and registration
    # conclusions are not manufactured from a partial record set.
    if not diagnostics:
        records = {record.path: record.document for record in source.records}
        graph_diagnostics = record_check.check_graph(records)
        diagnostics.extend(graph_diagnostics)
        diagnostics.extend(
            _registration_diagnostics(
                inventory, theory_approved, package_approved, product
            )
        )

    diagnostics.sort(key=record_check.Diagnostic.sort_key)
    return RegistrationObservation(package, inventory, tuple(diagnostics))


def _project_package_registration(
    observation: graph.GraphObservation,
    *,
    authority: graph.ManifestAuthority,
    theory_source: str,
    package: str,
    product: str,
) -> RegistrationObservation:
    """Internally project registration from an actor-owned captured graph.

    Actor wrappers must authenticate and capture the complete graph before using this
    non-accepting seam. It deliberately performs no source read, execution, policy
    resolution, or product-authority decision.
    """

    if not authority.ok:
        return RegistrationObservation(package, (), authority.diagnostics)

    sources = {item.source_id: item for item in authority.sources}
    declared_theory = sources.get(theory_source)
    if declared_theory is None:
        return _selector_observation(
            package,
            "REGISTRATION_UNKNOWN_THEORY_SOURCE",
            f"no {product} theory source selector for {theory_source!r}",
        )
    if not declared_theory.roles.issubset(_THEORY_ROLES):
        return _selector_observation(
            package,
            "REGISTRATION_THEORY_SOURCE_ROLE_MISMATCH",
            f"{product} theory source {theory_source!r} does not permit only "
            "theory-authored/dependency roles",
        )

    declared_package = sources.get(package)
    if declared_package is None:
        return _selector_observation(
            package,
            "REGISTRATION_UNKNOWN_PACKAGE_SOURCE",
            f"no {product} package source selector for {package!r}",
        )
    if not declared_package.roles.issubset(_PACKAGE_ROLES):
        return _selector_observation(
            package,
            "REGISTRATION_PACKAGE_SOURCE_ROLE_MISMATCH",
            f"{product} package source {package!r} does not permit only "
            "package-authored roles",
        )
    if not observation.ok:
        return RegistrationObservation(package, (), observation.diagnostics)

    records = tuple(
        sorted(
            (
                RegistrationRecord(
                    record.address,
                    (
                        "theory/"
                        if record.source == theory_source
                        else "package/"
                    )
                    + record.path.split("/", 1)[-1],
                    record.sha256,
                    record.role
                    or (
                        "theory-authored"
                        if record.source == theory_source
                        else "package-authored"
                    ),
                )
                for record in observation.records
                if record.source in {theory_source, package}
            ),
            key=lambda item: (item.address, item.path, item.sha256, item.role),
        )
    )
    return RegistrationObservation(package, records, ())


def inspect_stack_package(
    theory_root: Path, package_root: Path, package: str
) -> RegistrationObservation:
    """Inspect the pinned Stack package surface without actor overrides."""

    if not _MANIFEST.ok:
        return RegistrationObservation(package, (), _MANIFEST.diagnostics)
    if package not in {"rust", "typescript"}:
        return _selector_observation(
            package,
            "REGISTRATION_UNKNOWN_SELECTOR",
            f"no Stack package registration selector for {package!r}",
        )
    return inspect_package_registration(
        theory_root,
        package_root,
        package,
        authority=_MANIFEST,
        theory_source="theory",
        product="Stack",
    )
