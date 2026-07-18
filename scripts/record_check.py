"""Offline schema and link validation for canonical semantic-package records.

This module is the durable record/link gate for Wave 2. It:

- loads the seven local JSON Schema files and validates each against the
  Draft 2020-12 metaschema, building a fully offline `referencing` registry
  keyed by each schema's declared ``$id`` (no network fetch is ever made,
  even for the ``https://example.invalid/...`` identifiers);
- schema-validates a record against the schema selected by its ``kind``
  field, using ``jsonschema`` 4.26.0 with an explicit ``FormatChecker`` so
  that ``format: date-time`` is actually asserted rather than merely
  annotated;
- classifies a schema failure into one exact, data-derived
  ``(code, json_pointer)`` diagnostic rather than surfacing a raw validator
  message;
- link-checks a graph of already schema-valid records: duplicate canonical
  addresses, duplicate local declaration IDs, exact `(kind, id, version)`
  reference resolution (dangling / wrong-kind / wrong-version), typed local
  declaration and profile-member resolution, and Claim/Evidence/
  ConsumerPolicy coherence.

Diagnostic ordering is deterministic: within one graph, diagnostics are
sorted by `(relative source path, JSON pointer, code)`.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import jsonschema
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
FIXTURES_DIR = ROOT / "fixtures" / "records"

SCHEMA_FILES = {
    "specification": "spec.schema.json",
    "realization": "realization.schema.json",
    "claim": "claim.schema.json",
    "evidence": "evidence.schema.json",
    "realizationProfile": "realization-profile.schema.json",
    "consumerPolicy": "consumer-policy.schema.json",
}
COMMON_SCHEMA_FILE = "common.schema.json"

DECLARATION_CATEGORY_FIELDS = [
    ("carriers", "carrier"),
    ("operations", "operation"),
    ("observations", "observation"),
    ("derivedObservations", "derivedObservation"),
    ("equivalences", "equivalence"),
    ("laws", "law"),
    ("resources", "resource"),
    ("performancePropositions", "performanceProposition"),
]


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Diagnostic:
    code: str
    path: str
    pointer: str
    message: str | None = None

    def format(self) -> str:
        if self.message is None:
            return f"{self.code} {self.pointer}"
        return f"{self.code} {self.path}{self.pointer}: {self.message}"

    def sort_key(self) -> tuple[str, str, str]:
        return (self.path, self.pointer, self.code)


def ptr(*parts: Any) -> str:
    if not parts:
        return "#"
    return "#/" + "/".join(str(p) for p in parts)


def join_ptr(base: str, *parts: Any) -> str:
    if not parts:
        return base
    suffix = "/".join(str(p) for p in parts)
    if base == "#":
        return "#/" + suffix
    return base + "/" + suffix


def fmt_tuple(ref: dict) -> str:
    return f"({ref.get('kind')}, {ref.get('id')}, {ref.get('version')})"


def fmt_tuple_list(refs: list[dict]) -> str:
    return "[" + ", ".join(fmt_tuple(r) for r in refs) + "]"


def address_of(ref: dict) -> tuple[str, str, str]:
    return (ref.get("kind"), ref.get("id"), ref.get("version"))


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------


class SchemaRegistry:
    def __init__(self) -> None:
        self.schemas: dict[str, dict] = {}
        self.metaschema_errors: list[str] = []
        self._load()

    def _load(self) -> None:
        filenames = set(SCHEMA_FILES.values()) | {COMMON_SCHEMA_FILE}
        resources = []
        for filename in sorted(filenames):
            path = SCHEMA_DIR / filename
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.schemas[filename] = schema
            try:
                jsonschema.Draft202012Validator.check_schema(schema)
            except jsonschema.exceptions.SchemaError as error:
                self.metaschema_errors.append(f"{filename}: {error.message}")
            resources.append((schema["$id"], Resource.from_contents(schema)))
        self.registry = Registry().with_resources(resources)

    def validator_for(self, kind: str) -> jsonschema.protocols.Validator:
        filename = SCHEMA_FILES[kind]
        schema = self.schemas[filename]
        return jsonschema.Draft202012Validator(
            schema, registry=self.registry, format_checker=jsonschema.FormatChecker()
        )


# ---------------------------------------------------------------------------
# Schema-failure classification
# ---------------------------------------------------------------------------


def _missing(instance: dict, required: list[str]) -> list[str]:
    return [f for f in required if f not in instance]


def _unknown(instance: dict, allowed: Iterable[str]) -> list[str]:
    allowed_set = set(allowed)
    return [k for k in instance.keys() if k not in allowed_set]


def _classify_reference_shape(
    instance: Any,
    base_pointer: str,
    required: list[str],
    code: str,
    kind_const: str | None = None,
) -> tuple[str, str] | None:
    if not isinstance(instance, dict):
        return ("SCHEMA_TYPE_MISMATCH", base_pointer)
    missing = _missing(instance, required)
    if missing:
        return (code, join_ptr(base_pointer, missing[0]))
    unknown = _unknown(instance, required)
    if unknown:
        return (code, join_ptr(base_pointer, unknown[0]))
    if kind_const is not None and instance.get("kind") != kind_const:
        return (code, base_pointer)
    return None


def _classify_descriptor_shape(
    instance: Any,
    base_pointer: str,
    required: list[str],
    allowed: list[str],
    code: str,
) -> tuple[str, str] | None:
    if not isinstance(instance, dict):
        return ("SCHEMA_TYPE_MISMATCH", base_pointer)
    missing = _missing(instance, required)
    if missing:
        return (code, base_pointer)
    unknown = _unknown(instance, allowed)
    if unknown:
        return (code, base_pointer)
    return None


def _classify_plain_object(
    instance: Any,
    base_pointer: str,
    required: list[str],
    allowed: list[str],
) -> tuple[str, str] | None:
    if not isinstance(instance, dict):
        return ("SCHEMA_TYPE_MISMATCH", base_pointer)
    missing = _missing(instance, required)
    if missing:
        return ("SCHEMA_MISSING_FIELD", join_ptr(base_pointer, missing[0]))
    unknown = _unknown(instance, allowed)
    if unknown:
        return ("SCHEMA_UNKNOWN_FIELD", join_ptr(base_pointer, unknown[0]))
    return None


def _classify_enum(instance: Any, base_pointer: str, allowed: list[str], code: str) -> tuple[str, str] | None:
    if instance not in allowed:
        return (code, base_pointer)
    return None


_SPEC_REF_REQUIRED = ["kind", "id", "version"]
_DECLARATION_REF_REQUIRED = ["specification", "declarationId"]
_PROFILE_MEMBER_REQUIRED = ["profile", "localId"]
_ADAPTER_SELECTOR_REQUIRED = ["id", "version"]
_ADAPTER_DESCRIPTOR_REQUIRED = ["id", "version", "protocol", "entrypoint", "assumptions"]


def _classify_declaration_reference(instance: Any, base_pointer: str) -> tuple[str, str] | None:
    if not isinstance(instance, dict):
        return ("SCHEMA_TYPE_MISMATCH", base_pointer)
    missing = _missing(instance, _DECLARATION_REF_REQUIRED)
    if missing:
        return ("SCHEMA_EXACT_REF", join_ptr(base_pointer, missing[0]))
    unknown = _unknown(instance, _DECLARATION_REF_REQUIRED)
    if unknown:
        return ("SCHEMA_EXACT_REF", join_ptr(base_pointer, unknown[0]))
    return _classify_reference_shape(
        instance["specification"], join_ptr(base_pointer, "specification"), _SPEC_REF_REQUIRED,
        "SCHEMA_EXACT_REF", kind_const="specification",
    )


def _classify_profile_member_reference(instance: Any, base_pointer: str) -> tuple[str, str] | None:
    if not isinstance(instance, dict):
        return ("SCHEMA_TYPE_MISMATCH", base_pointer)
    missing = _missing(instance, _PROFILE_MEMBER_REQUIRED)
    if missing:
        return ("SCHEMA_EXACT_REF", join_ptr(base_pointer, missing[0]))
    unknown = _unknown(instance, _PROFILE_MEMBER_REQUIRED)
    if unknown:
        return ("SCHEMA_EXACT_REF", join_ptr(base_pointer, unknown[0]))
    return _classify_reference_shape(
        instance["profile"], join_ptr(base_pointer, "profile"), _SPEC_REF_REQUIRED,
        "SCHEMA_EXACT_REF", kind_const="realizationProfile",
    )


def _classify_subject_reference(instance: Any, base_pointer: str) -> tuple[str, str] | None:
    if not isinstance(instance, dict) or instance.get("kind") not in ("specification", "realization"):
        return ("SCHEMA_SUBJECT_KIND", base_pointer)
    code = "SCHEMA_EXACT_REF"
    return _classify_reference_shape(instance, base_pointer, _SPEC_REF_REQUIRED, code, kind_const=instance["kind"])


def _classify_ref_array(items: Any, base_pointer: str, kind_const: str) -> tuple[str, str] | None:
    if items is None:
        return None
    if not isinstance(items, list):
        return ("SCHEMA_TYPE_MISMATCH", base_pointer)
    for index, item in enumerate(items):
        result = _classify_reference_shape(
            item, join_ptr(base_pointer, index), _SPEC_REF_REQUIRED, "SCHEMA_EXACT_REF", kind_const=kind_const
        )
        if result:
            return result
    return None


def _classify_object_array(
    items: Any,
    base_pointer: str,
    item_classifier: Any,
) -> tuple[str, str] | None:
    """Classify a field expected to be a JSON array of objects.

    Guards the container's own type before iterating, so a wrong container type
    (e.g. an object where an array is required) is reported at `base_pointer`
    itself rather than inventing an element pointer by iterating whatever the
    wrong-typed value happens to yield (e.g. dict keys via ``enumerate``).
    """
    if items is None:
        return None
    if not isinstance(items, list):
        return ("SCHEMA_TYPE_MISMATCH", base_pointer)
    for index, item in enumerate(items):
        result = item_classifier(item, join_ptr(base_pointer, index))
        if result:
            return result
    return None


_IMPLEMENTATION_REQUIRED = [
    "language", "languageVersion", "target", "runtime", "interfaceMechanism",
    "buildSystem", "buildInstructions", "executionInstructions",
]
_IMPLEMENTATION_ALLOWED = _IMPLEMENTATION_REQUIRED + ["abi", "memoryModel"]

_CARRIER_REQUIRED = ["id"]
_CARRIER_ALLOWED = ["id", "description"]
_OPERATION_REQUIRED = ["id", "signature"]
_OPERATION_ALLOWED = ["id", "signature"]
_DERIVED_OBS_REQUIRED = ["id", "definition"]
_DERIVED_OBS_ALLOWED = ["id", "definition"]
_EQUIVALENCE_REQUIRED = ["id", "carrier", "definition"]
_EQUIVALENCE_ALLOWED = ["id", "carrier", "definition"]
_LAW_REQUIRED = ["id", "statement"]
_LAW_ALLOWED = ["id", "statement"]
_RESOURCE_REQUIRED = ["id", "rule"]
_RESOURCE_ALLOWED = ["id", "rule"]
_EFFECT_REQUIRED = ["id", "default"]
_EFFECT_ALLOWED = ["id", "forbidden", "required", "permitted", "optional", "default"]
_EFFECT_DISPOSITIONS = ["forbidden", "required", "permitted", "optional", "unspecified"]

_PERF_PROP_REQUIRED = ["id", "operationFamily", "workload", "costMeasure", "predicate", "permittedEvidenceMethods"]
_PERF_PROP_ALLOWED = _PERF_PROP_REQUIRED


def _classify_performance_proposition(instance: Any, base_pointer: str) -> tuple[str, str] | None:
    if not isinstance(instance, dict):
        return ("SCHEMA_TYPE_MISMATCH", base_pointer)
    if "workload" not in instance or "costMeasure" not in instance:
        return ("SCHEMA_PERFORMANCE_SCOPE", base_pointer)
    missing = _missing(instance, _PERF_PROP_REQUIRED)
    if missing:
        return ("SCHEMA_MISSING_FIELD", join_ptr(base_pointer, missing[0]))
    unknown = _unknown(instance, _PERF_PROP_ALLOWED)
    if unknown:
        return ("SCHEMA_UNKNOWN_FIELD", join_ptr(base_pointer, unknown[0]))
    for field in ("workload", "costMeasure"):
        result = _classify_profile_member_reference(instance[field], join_ptr(base_pointer, field))
        if result:
            return result
    return None


_SPEC_TOP_REQUIRED = ["kind", "id", "version"]
_SPEC_TOP_ALLOWED = _SPEC_TOP_REQUIRED + [
    "imports", "carriers", "operations", "observations", "derivedObservations",
    "equivalences", "laws", "effects", "resources", "performancePropositions",
]
_SPEC_ASPECTS = [
    "carriers", "operations", "observations", "derivedObservations", "equivalences",
    "laws", "effects", "resources", "performancePropositions",
]


def classify_specification(instance: dict) -> tuple[str, str] | None:
    result = _classify_plain_object(instance, "#", _SPEC_TOP_REQUIRED, _SPEC_TOP_ALLOWED)
    if result:
        return result
    if not any(aspect in instance for aspect in _SPEC_ASPECTS):
        return ("SCHEMA_EMPTY_SPECIFICATION", "#")

    result = _classify_ref_array(instance.get("imports"), ptr("imports"), "specification")
    if result:
        return result

    result = _classify_object_array(
        instance.get("carriers"), ptr("carriers"),
        lambda item, p: _classify_plain_object(item, p, _CARRIER_REQUIRED, _CARRIER_ALLOWED),
    )
    if result:
        return result
    for field in ("operations", "observations"):
        result = _classify_object_array(
            instance.get(field), ptr(field),
            lambda item, p: _classify_plain_object(item, p, _OPERATION_REQUIRED, _OPERATION_ALLOWED),
        )
        if result:
            return result
    result = _classify_object_array(
        instance.get("derivedObservations"), ptr("derivedObservations"),
        lambda item, p: _classify_plain_object(item, p, _DERIVED_OBS_REQUIRED, _DERIVED_OBS_ALLOWED),
    )
    if result:
        return result
    result = _classify_object_array(
        instance.get("equivalences"), ptr("equivalences"),
        lambda item, p: _classify_plain_object(item, p, _EQUIVALENCE_REQUIRED, _EQUIVALENCE_ALLOWED),
    )
    if result:
        return result
    result = _classify_object_array(
        instance.get("laws"), ptr("laws"),
        lambda item, p: _classify_plain_object(item, p, _LAW_REQUIRED, _LAW_ALLOWED),
    )
    if result:
        return result
    if "effects" in instance:
        effects = instance["effects"]
        result = _classify_plain_object(effects, ptr("effects"), _EFFECT_REQUIRED, _EFFECT_ALLOWED)
        if result:
            return result
        if isinstance(effects, dict) and "default" in effects and effects["default"] not in _EFFECT_DISPOSITIONS:
            return ("SCHEMA_UNKNOWN_FIELD", ptr("effects", "default"))
    result = _classify_object_array(
        instance.get("resources"), ptr("resources"),
        lambda item, p: _classify_plain_object(item, p, _RESOURCE_REQUIRED, _RESOURCE_ALLOWED),
    )
    if result:
        return result
    result = _classify_object_array(
        instance.get("performancePropositions"), ptr("performancePropositions"),
        _classify_performance_proposition,
    )
    if result:
        return result
    return None


_REALIZATION_TOP_REQUIRED = [
    "kind", "id", "version", "specification", "adapter", "implementation",
    "capabilities", "limitations", "supportedProfiles",
]
_REALIZATION_TOP_ALLOWED = _REALIZATION_TOP_REQUIRED


def classify_realization(instance: dict) -> tuple[str, str] | None:
    result = _classify_plain_object(instance, "#", _REALIZATION_TOP_REQUIRED, _REALIZATION_TOP_ALLOWED)
    if result:
        return result
    result = _classify_reference_shape(
        instance["specification"], ptr("specification"), _SPEC_REF_REQUIRED, "SCHEMA_EXACT_REF",
        kind_const="specification",
    )
    if result:
        return result
    result = _classify_descriptor_shape(
        instance["adapter"], ptr("adapter"), _ADAPTER_DESCRIPTOR_REQUIRED, _ADAPTER_DESCRIPTOR_REQUIRED,
        "SCHEMA_ADAPTER_DESCRIPTOR",
    )
    if result:
        return result
    result = _classify_plain_object(instance["implementation"], ptr("implementation"), _IMPLEMENTATION_REQUIRED, _IMPLEMENTATION_ALLOWED)
    if result:
        return result
    return _classify_ref_array(instance.get("supportedProfiles"), ptr("supportedProfiles"), "realizationProfile")


_CLAIM_TOP_REQUIRED = [
    "kind", "id", "version", "subject", "governingSpecification", "proposition",
    "concern", "scope", "assumptions", "exclusions", "applicableProfiles", "state",
]
_CLAIM_TOP_ALLOWED = _CLAIM_TOP_REQUIRED
_CLAIM_LIFECYCLE_STATES = ["draft", "active", "retired", "withdrawn"]


def classify_claim(instance: dict) -> tuple[str, str] | None:
    result = _classify_plain_object(instance, "#", _CLAIM_TOP_REQUIRED, _CLAIM_TOP_ALLOWED)
    if result:
        return result
    result = _classify_subject_reference(instance["subject"], ptr("subject"))
    if result:
        return result
    result = _classify_reference_shape(
        instance["governingSpecification"], ptr("governingSpecification"), _SPEC_REF_REQUIRED,
        "SCHEMA_EXACT_REF", kind_const="specification",
    )
    if result:
        return result
    result = _classify_declaration_reference(instance["proposition"], ptr("proposition"))
    if result:
        return result
    result = _classify_ref_array(instance.get("applicableProfiles"), ptr("applicableProfiles"), "realizationProfile")
    if result:
        return result
    return _classify_enum(instance["state"], ptr("state"), _CLAIM_LIFECYCLE_STATES, "SCHEMA_CLAIM_STATE")


_EVIDENCE_TOP_REQUIRED = [
    "kind", "id", "version", "claim", "specification", "scope", "mechanism", "result",
    "reviewState", "method", "environment", "freshness", "assumptions", "exclusions",
    "applicability", "provenance",
]
_EVIDENCE_TOP_ALLOWED = _EVIDENCE_TOP_REQUIRED + ["realization", "adapter"]
_EVIDENCE_RESULTS = ["supports", "challenges", "inconclusive", "error"]
_EVIDENCE_REVIEW_STATES = ["unverified", "pending", "accepted", "rejected", "superseded", "revoked"]
_APPLICABILITY_REQUIRED = ["profiles"]
_APPLICABILITY_ALLOWED = ["profiles", "parameters"]
_FRESHNESS_REQUIRED = ["producedAt"]
_FRESHNESS_ALLOWED = ["producedAt", "expiresAt"]

# The same FormatChecker instance/semantics the SchemaRegistry validators use for
# `format: date-time`, so a classification-time recheck can never diverge from the
# validation-time verdict that made a record schema-invalid in the first place.
_DATE_TIME_FORMAT_CHECKER = jsonschema.FormatChecker()


def _is_valid_date_time(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return _DATE_TIME_FORMAT_CHECKER.conforms(value, "date-time")


def classify_evidence(instance: dict) -> tuple[str, str] | None:
    result = _classify_plain_object(instance, "#", _EVIDENCE_TOP_REQUIRED, _EVIDENCE_TOP_ALLOWED)
    if result:
        return result

    scope = instance.get("scope")
    has_realization = "realization" in instance
    has_adapter = "adapter" in instance
    if scope == "specification" and (has_realization or has_adapter):
        return ("SCHEMA_RUNTIME_SCOPE_PAIR", ptr("adapter") if has_adapter else ptr("realization"))
    if scope == "realization" and not (has_realization and has_adapter):
        return ("SCHEMA_RUNTIME_SCOPE_PAIR", ptr("adapter") if not has_adapter else ptr("realization"))

    result = _classify_reference_shape(
        instance["claim"], ptr("claim"), _SPEC_REF_REQUIRED, "SCHEMA_EXACT_REF", kind_const="claim"
    )
    if result:
        return result
    result = _classify_reference_shape(
        instance["specification"], ptr("specification"), _SPEC_REF_REQUIRED, "SCHEMA_EXACT_REF",
        kind_const="specification",
    )
    if result:
        return result
    if scope not in ("specification", "realization"):
        return ("SCHEMA_UNKNOWN_FIELD", ptr("scope"))
    if has_realization:
        result = _classify_reference_shape(
            instance["realization"], ptr("realization"), _SPEC_REF_REQUIRED, "SCHEMA_EXACT_REF",
            kind_const="realization",
        )
        if result:
            return result
    if has_adapter:
        result = _classify_reference_shape(
            instance["adapter"], ptr("adapter"), _ADAPTER_SELECTOR_REQUIRED, "SCHEMA_ADAPTER_SELECTOR"
        )
        if result:
            return result
    if instance["result"] not in _EVIDENCE_RESULTS:
        return ("SCHEMA_RESULT_ENUM", ptr("result"))
    if instance["reviewState"] not in _EVIDENCE_REVIEW_STATES:
        return ("SCHEMA_REVIEW_STATE_ENUM", ptr("reviewState"))
    result = _classify_plain_object(
        instance["applicability"], ptr("applicability"), _APPLICABILITY_REQUIRED, _APPLICABILITY_ALLOWED
    )
    if result:
        return result
    result = _classify_ref_array(instance["applicability"].get("profiles"), ptr("applicability", "profiles"), "realizationProfile")
    if result:
        return result
    result = _classify_plain_object(
        instance["freshness"], ptr("freshness"), _FRESHNESS_REQUIRED, _FRESHNESS_ALLOWED
    )
    if result:
        return result
    for field in ("producedAt", "expiresAt"):
        if field in instance["freshness"] and not _is_valid_date_time(instance["freshness"][field]):
            return ("SCHEMA_DATE_TIME_FORMAT", ptr("freshness", field))
    return None


_REALIZATION_PROFILE_TOP_REQUIRED = ["kind", "id", "version"]
_REALIZATION_PROFILE_TOP_ALLOWED = _REALIZATION_PROFILE_TOP_REQUIRED + [
    "platform", "hostCapabilities", "scale", "concurrency", "trust", "portability",
    "workloads", "costMeasures",
]
_WORKLOAD_REQUIRED = ["id", "startingState", "sizeFunction", "definition"]
_WORKLOAD_ALLOWED = _WORKLOAD_REQUIRED
_COST_MEASURE_REQUIRED = ["id", "unit", "aggregation", "instrumentation"]
_COST_MEASURE_ALLOWED = _COST_MEASURE_REQUIRED


def classify_realization_profile(instance: dict) -> tuple[str, str] | None:
    result = _classify_plain_object(instance, "#", _REALIZATION_PROFILE_TOP_REQUIRED, _REALIZATION_PROFILE_TOP_ALLOWED)
    if result:
        return result
    result = _classify_object_array(
        instance.get("workloads"), ptr("workloads"),
        lambda item, p: _classify_plain_object(item, p, _WORKLOAD_REQUIRED, _WORKLOAD_ALLOWED),
    )
    if result:
        return result
    result = _classify_object_array(
        instance.get("costMeasures"), ptr("costMeasures"),
        lambda item, p: _classify_plain_object(item, p, _COST_MEASURE_REQUIRED, _COST_MEASURE_ALLOWED),
    )
    if result:
        return result
    return None


_POLICY_TOP_REQUIRED = ["kind", "id", "version", "specification", "profile", "concerns", "prohibitions"]
_POLICY_TOP_ALLOWED = _POLICY_TOP_REQUIRED
_CONCERN_PRIORITIES = ["required", "preferred", "optional", "ignored"]
_CONCERN_ENTRY_REQUIRED = ["concern", "priority"]
_CONCERN_ENTRY_ALLOWED = ["concern", "priority", "acceptedMechanisms", "minimumAssurance"]
_PROHIBITION_ENTRY_REQUIRED = ["proposition", "description", "acceptedEvidenceScope"]
_PROHIBITION_ENTRY_ALLOWED = ["proposition", "description", "eventPattern", "acceptedEvidenceScope"]


def classify_consumer_policy(instance: dict) -> tuple[str, str] | None:
    result = _classify_plain_object(instance, "#", _POLICY_TOP_REQUIRED, _POLICY_TOP_ALLOWED)
    if result:
        return result
    result = _classify_reference_shape(
        instance["specification"], ptr("specification"), _SPEC_REF_REQUIRED, "SCHEMA_EXACT_REF",
        kind_const="specification",
    )
    if result:
        return result
    result = _classify_reference_shape(
        instance["profile"], ptr("profile"), _SPEC_REF_REQUIRED, "SCHEMA_EXACT_REF",
        kind_const="realizationProfile",
    )
    if result:
        return result
    def _classify_concern_entry(item: Any, p: str) -> tuple[str, str] | None:
        result = _classify_plain_object(item, p, _CONCERN_ENTRY_REQUIRED, _CONCERN_ENTRY_ALLOWED)
        if result:
            return result
        if item.get("priority") not in _CONCERN_PRIORITIES:
            return ("SCHEMA_PRIORITY_ENUM", join_ptr(p, "priority"))
        return None

    result = _classify_object_array(instance.get("concerns"), ptr("concerns"), _classify_concern_entry)
    if result:
        return result

    def _classify_prohibition_entry(item: Any, p: str) -> tuple[str, str] | None:
        result = _classify_plain_object(item, p, _PROHIBITION_ENTRY_REQUIRED, _PROHIBITION_ENTRY_ALLOWED)
        if result:
            return result
        return _classify_declaration_reference(item["proposition"], join_ptr(p, "proposition"))

    result = _classify_object_array(instance.get("prohibitions"), ptr("prohibitions"), _classify_prohibition_entry)
    if result:
        return result
    return None


_CLASSIFIERS = {
    "specification": classify_specification,
    "realization": classify_realization,
    "claim": classify_claim,
    "evidence": classify_evidence,
    "realizationProfile": classify_realization_profile,
    "consumerPolicy": classify_consumer_policy,
}


def validate_record(schemas: SchemaRegistry, path: str, instance: Any) -> Diagnostic | None:
    if not isinstance(instance, dict) or "kind" not in instance:
        return Diagnostic("SCHEMA_MISSING_KIND", path, "#")
    kind = instance["kind"]
    if not isinstance(kind, str):
        return Diagnostic("SCHEMA_KIND_TYPE", path, ptr("kind"))
    if kind not in SCHEMA_FILES:
        return Diagnostic("SCHEMA_UNKNOWN_KIND", path, "#")
    validator = schemas.validator_for(kind)
    if validator.is_valid(instance):
        return None
    result = _CLASSIFIERS[kind](instance)
    if result is None:
        result = ("SCHEMA_INVALID", "#")
    code, pointer = result
    return Diagnostic(code, path, pointer)


# ---------------------------------------------------------------------------
# Link checking
# ---------------------------------------------------------------------------


class Graph:
    """An isolated, already schema-valid set of records keyed by relative path."""

    def __init__(self, records: dict[str, dict]) -> None:
        self.records = records
        self.by_address: dict[tuple[str, str, str], dict] = {}
        self.by_id_version: dict[tuple[str, str], set[str]] = {}
        self.by_kind_id: dict[tuple[str, str], set[str]] = {}
        self.duplicates: list[Diagnostic] = []
        self._index()

    def _index(self) -> None:
        for path in sorted(self.records):
            record = self.records[path]
            address = (record["kind"], record["id"], record["version"])
            if address in self.by_address:
                self.duplicates.append(
                    Diagnostic("LINK_DUPLICATE_ADDRESS", path, "#", f"requested {fmt_tuple(record)}")
                )
                continue
            self.by_address[address] = record
            self.by_id_version.setdefault((address[1], address[2]), set()).add(address[0])
            self.by_kind_id.setdefault((address[0], address[1]), set()).add(address[2])

    def resolve(self, ref: dict, path: str, pointer: str) -> tuple[list[Diagnostic], dict | None]:
        """Resolve an exact (kind, id, version) reference.

        A missing exact address can have two independent near-miss candidates at
        once: a record at the requested (id, version) but the wrong kind, and a
        record of the requested kind and id but at a different version. Both are
        real, independently actionable observations, so both are returned rather
        than only the first one found.
        """
        address = address_of(ref)
        record = self.by_address.get(address)
        if record is not None:
            return [], record

        diagnostics: list[Diagnostic] = []
        found_versions = self.by_kind_id.get((address[0], address[1]))
        if found_versions:
            loaded_versions = ", ".join(sorted(found_versions))
            label = "loaded version is" if len(found_versions) == 1 else "loaded versions are"
            diagnostics.append(
                Diagnostic(
                    "LINK_VERSION_MISMATCH", path, pointer,
                    f"requested {fmt_tuple(ref)}, {label} {loaded_versions}",
                )
            )
        found_kinds = self.by_id_version.get((address[1], address[2]))
        if found_kinds:
            loaded_kinds = ", ".join(sorted(found_kinds))
            label = "loaded kind is" if len(found_kinds) == 1 else "loaded kinds are"
            diagnostics.append(
                Diagnostic(
                    "LINK_WRONG_KIND_REFERENCE", path, pointer,
                    f"requested {fmt_tuple(ref)}, {label} {loaded_kinds}",
                )
            )
        if not diagnostics:
            diagnostics.append(
                Diagnostic("LINK_DANGLING_REFERENCE", path, pointer, f"requested {fmt_tuple(ref)}")
            )
        return diagnostics, None


def _local_declaration_index(spec: dict) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for field, category in DECLARATION_CATEGORY_FIELDS:
        for item in spec.get(field, []):
            declaration_id = item.get("id")
            if declaration_id is not None:
                index.setdefault(declaration_id, set()).add(category)
    effects = spec.get("effects")
    if isinstance(effects, dict):
        declaration_id = effects.get("id")
        if declaration_id is not None:
            index.setdefault(declaration_id, set()).add("effect")
    return index


def _duplicate_declaration_diagnostics(path: str, spec: dict) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()
    for field, _category in DECLARATION_CATEGORY_FIELDS:
        for index, item in enumerate(spec.get(field, [])):
            declaration_id = item.get("id")
            if declaration_id is None:
                continue
            if declaration_id in seen:
                diagnostics.append(
                    Diagnostic(
                        "LINK_DUPLICATE_DECLARATION_ID", path, ptr(field, index, "id"),
                        f"requested local ID {declaration_id} in {fmt_tuple(spec)}",
                    )
                )
            else:
                seen.add(declaration_id)
    effects = spec.get("effects")
    if isinstance(effects, dict):
        declaration_id = effects.get("id")
        if declaration_id is not None:
            if declaration_id in seen:
                diagnostics.append(
                    Diagnostic(
                        "LINK_DUPLICATE_DECLARATION_ID", path, ptr("effects", "id"),
                        f"requested local ID {declaration_id} in {fmt_tuple(spec)}",
                    )
                )
            else:
                seen.add(declaration_id)
    return diagnostics


def _resolve_local_declaration(
    spec: dict, requested_id: str, path: str, pointer: str, expected_category: str | None = None
) -> Diagnostic | None:
    index = _local_declaration_index(spec)
    actual_categories = index.get(requested_id)
    if actual_categories is None:
        return Diagnostic(
            "LINK_DANGLING_DECLARATION", path, pointer, f"requested local ID {requested_id} in {fmt_tuple(spec)}"
        )
    if expected_category is not None and expected_category not in actual_categories:
        found = ", ".join(sorted(actual_categories))
        return Diagnostic(
            "LINK_DECLARATION_KIND_MISMATCH", path, pointer,
            f"requested local ID {requested_id} as {expected_category} in {fmt_tuple(spec)}, found {found}",
        )
    return None


def _profile_member_index(profile: dict) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for item in profile.get("workloads", []):
        member_id = item.get("id")
        if member_id is not None:
            index.setdefault(member_id, set()).add("workload")
    for item in profile.get("costMeasures", []):
        member_id = item.get("id")
        if member_id is not None:
            index.setdefault(member_id, set()).add("costMeasure")
    return index


def _resolve_profile_member(
    profile: dict, requested_id: str, expected_role: str, path: str, pointer: str
) -> Diagnostic | None:
    index = _profile_member_index(profile)
    actual_roles = index.get(requested_id)
    if actual_roles is None:
        return Diagnostic(
            "LINK_DANGLING_PROFILE_MEMBER", path, pointer,
            f"requested local ID {requested_id} in {fmt_tuple(profile)}",
        )
    if expected_role not in actual_roles:
        found = ", ".join(sorted(actual_roles))
        return Diagnostic(
            "LINK_PROFILE_MEMBER_KIND_MISMATCH", path, pointer,
            f"requested local ID {requested_id} as {expected_role} in {fmt_tuple(profile)}, found {found}",
        )
    return None


def _check_specification(graph: Graph, path: str, spec: dict) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_duplicate_declaration_diagnostics(path, spec))

    for index, ref in enumerate(spec.get("imports", [])):
        errors, _ = graph.resolve(ref, path, ptr("imports", index))
        diagnostics.extend(errors)

    for index, item in enumerate(spec.get("equivalences", [])):
        carrier_id = item.get("carrier")
        if carrier_id is None:
            continue
        error = _resolve_local_declaration(spec, carrier_id, path, ptr("equivalences", index, "carrier"), "carrier")
        if error:
            diagnostics.append(error)

    for prop_index, item in enumerate(spec.get("performancePropositions", [])):
        for member_index, operation_id in enumerate(item.get("operationFamily", [])):
            error = _resolve_local_declaration(
                spec, operation_id, path,
                ptr("performancePropositions", prop_index, "operationFamily", member_index), "operation",
            )
            if error:
                diagnostics.append(error)
        for role, field in (("workload", "workload"), ("costMeasure", "costMeasure")):
            member = item.get(field)
            if not isinstance(member, dict):
                continue
            base_pointer = ptr("performancePropositions", prop_index, field)
            profile_ref = member.get("profile")
            local_id = member.get("localId")
            if not isinstance(profile_ref, dict) or local_id is None:
                continue
            errors, profile_record = graph.resolve(profile_ref, path, join_ptr(base_pointer, "profile"))
            if errors:
                diagnostics.extend(errors)
                continue
            error = _resolve_profile_member(profile_record, local_id, role, path, join_ptr(base_pointer, "localId"))
            if error:
                diagnostics.append(error)
    return diagnostics


def _check_realization(graph: Graph, path: str, realization: dict) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    spec_ref = realization.get("specification")
    if isinstance(spec_ref, dict):
        errors, _ = graph.resolve(spec_ref, path, ptr("specification"))
        diagnostics.extend(errors)
    for index, ref in enumerate(realization.get("supportedProfiles", [])):
        errors, _ = graph.resolve(ref, path, ptr("supportedProfiles", index))
        diagnostics.extend(errors)
    return diagnostics


def _check_claim(graph: Graph, path: str, claim: dict) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    subject = claim.get("subject", {})
    errors, subject_record = graph.resolve(subject, path, ptr("subject"))
    diagnostics.extend(errors)

    governing = claim.get("governingSpecification")
    errors, _ = graph.resolve(governing, path, ptr("governingSpecification"))
    diagnostics.extend(errors)

    if subject.get("kind") == "specification":
        if governing != subject:
            diagnostics.append(
                Diagnostic(
                    "LINK_CLAIM_SPECIFICATION_MISMATCH", path, ptr("governingSpecification"),
                    f"requested {fmt_tuple(governing)}, subject governs {fmt_tuple(subject)}",
                )
            )
    elif subject.get("kind") == "realization" and subject_record is not None:
        subject_governs = subject_record.get("specification")
        if governing != subject_governs:
            diagnostics.append(
                Diagnostic(
                    "LINK_CLAIM_SPECIFICATION_MISMATCH", path, ptr("governingSpecification"),
                    f"requested {fmt_tuple(governing)}, subject Realization governs {fmt_tuple(subject_governs)}",
                )
            )

    proposition = claim.get("proposition", {})
    prop_spec = proposition.get("specification")
    if isinstance(prop_spec, dict):
        errors, prop_spec_record = graph.resolve(prop_spec, path, ptr("proposition", "specification"))
        diagnostics.extend(errors)
        if not errors and prop_spec != governing:
            diagnostics.append(
                Diagnostic(
                    "LINK_CLAIM_PROPOSITION_SPECIFICATION_MISMATCH", path, ptr("proposition", "specification"),
                    f"requested {fmt_tuple(prop_spec)}, governingSpecification is {fmt_tuple(governing)}",
                )
            )
        if not errors and prop_spec_record is not None:
            declaration_id = proposition.get("declarationId")
            if declaration_id is not None:
                decl_error = _resolve_local_declaration(
                    prop_spec_record, declaration_id, path, ptr("proposition", "declarationId")
                )
                if decl_error:
                    diagnostics.append(decl_error)

    for index, ref in enumerate(claim.get("applicableProfiles", [])):
        errors, _ = graph.resolve(ref, path, ptr("applicableProfiles", index))
        diagnostics.extend(errors)

    return diagnostics


def _check_evidence(graph: Graph, path: str, evidence: dict) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    claim_ref = evidence.get("claim")
    errors, claim_record = graph.resolve(claim_ref, path, ptr("claim"))
    diagnostics.extend(errors)

    claim_subject = claim_record.get("subject", {}) if claim_record is not None else {}
    if claim_subject.get("kind") == "realization" and evidence.get("scope") != "realization":
        diagnostics.append(
            Diagnostic(
                "LINK_EVIDENCE_RUNTIME_SCOPE_REQUIRED", path, ptr("scope"),
                f"requested realization scope with matching Realization and adapter for Claim subject "
                f"{fmt_tuple(claim_subject)}",
            )
        )

    spec_ref = evidence.get("specification")
    spec_errors, _ = graph.resolve(spec_ref, path, ptr("specification"))
    diagnostics.extend(spec_errors)
    if not spec_errors and claim_record is not None:
        claim_governs = claim_record.get("governingSpecification")
        if spec_ref != claim_governs:
            diagnostics.append(
                Diagnostic(
                    "LINK_EVIDENCE_SPECIFICATION_MISMATCH", path, ptr("specification"),
                    f"requested {fmt_tuple(spec_ref)}, Claim governs {fmt_tuple(claim_governs)}",
                )
            )

    realization_ref = evidence.get("realization")
    realization_record = None
    if isinstance(realization_ref, dict):
        errors, realization_record = graph.resolve(realization_ref, path, ptr("realization"))
        diagnostics.extend(errors)
        if not errors and claim_record is not None:
            if claim_subject.get("kind") == "realization" and realization_ref != claim_subject:
                diagnostics.append(
                    Diagnostic(
                        "LINK_EVIDENCE_REALIZATION_MISMATCH", path, ptr("realization"),
                        f"requested {fmt_tuple(realization_ref)}, claim subject is {fmt_tuple(claim_subject)}",
                    )
                )
        if not errors and realization_record is not None and not spec_errors:
            realization_governs = realization_record.get("specification")
            if realization_governs != spec_ref:
                diagnostics.append(
                    Diagnostic(
                        "LINK_EVIDENCE_REALIZATION_SPECIFICATION_MISMATCH", path, ptr("realization"),
                        f"requested {fmt_tuple(realization_ref)}, Realization governs {fmt_tuple(realization_governs)} "
                        f"but Evidence governs {fmt_tuple(spec_ref)}",
                    )
                )

    adapter_ref = evidence.get("adapter")
    if isinstance(adapter_ref, dict) and realization_record is not None:
        declared_adapter = realization_record.get("adapter", {})
        if (adapter_ref.get("id"), adapter_ref.get("version")) != (
            declared_adapter.get("id"), declared_adapter.get("version")
        ):
            diagnostics.append(
                Diagnostic(
                    "LINK_EVIDENCE_ADAPTER_MISMATCH", path, ptr("adapter"),
                    f"requested adapter ({adapter_ref.get('id')}, {adapter_ref.get('version')}), "
                    f"Realization descriptor is ({declared_adapter.get('id')}, {declared_adapter.get('version')})",
                )
            )

    applicability = evidence.get("applicability", {})
    profiles = applicability.get("profiles", [])
    for index, ref in enumerate(profiles):
        errors, _ = graph.resolve(ref, path, ptr("applicability", "profiles", index))
        diagnostics.extend(errors)
    if claim_record is not None:
        claim_profiles = claim_record.get("applicableProfiles", [])
        evidence_set = {address_of(r) for r in profiles}
        claim_set = {address_of(r) for r in claim_profiles}
        if evidence_set != claim_set:
            if len(profiles) == 1 and len(claim_profiles) == 1:
                diagnostics.append(
                    Diagnostic(
                        "LINK_EVIDENCE_PROFILE_MISMATCH", path, ptr("applicability", "profiles", 0),
                        f"requested {fmt_tuple(profiles[0])}, Claim applicableProfiles contains {fmt_tuple(claim_profiles[0])}",
                    )
                )
            else:
                diagnostics.append(
                    Diagnostic(
                        "LINK_EVIDENCE_PROFILE_MISMATCH", path, ptr("applicability", "profiles"),
                        f"requested exact set {fmt_tuple_list(profiles)}, "
                        f"Claim applicableProfiles is {fmt_tuple_list(claim_profiles)}",
                    )
                )

    return diagnostics


def _check_consumer_policy(graph: Graph, path: str, policy: dict) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    spec_ref = policy.get("specification")
    errors, _ = graph.resolve(spec_ref, path, ptr("specification"))
    diagnostics.extend(errors)

    profile_ref = policy.get("profile")
    errors, _ = graph.resolve(profile_ref, path, ptr("profile"))
    diagnostics.extend(errors)

    for index, entry in enumerate(policy.get("prohibitions", [])):
        proposition = entry.get("proposition", {})
        prop_spec = proposition.get("specification")
        if not isinstance(prop_spec, dict):
            continue
        base_pointer = ptr("prohibitions", index, "proposition")
        errors, prop_spec_record = graph.resolve(prop_spec, path, join_ptr(base_pointer, "specification"))
        if errors:
            diagnostics.extend(errors)
            continue
        if prop_spec != spec_ref:
            diagnostics.append(
                Diagnostic(
                    "LINK_POLICY_SPECIFICATION_MISMATCH", path, join_ptr(base_pointer, "specification"),
                    f"requested {fmt_tuple(prop_spec)}, ConsumerPolicy specification is {fmt_tuple(spec_ref)}",
                )
            )
            continue
        declaration_id = proposition.get("declarationId")
        if declaration_id is None:
            continue
        event_pattern = entry.get("eventPattern")
        # A prohibition that selects an eventPattern is only meaningful against the
        # Specification's single effect declaration; any other declaration role
        # (e.g. a law) cannot carry event dispositions at all.
        expected_category = "effect" if event_pattern is not None else None
        decl_error = _resolve_local_declaration(
            prop_spec_record, declaration_id, path, join_ptr(base_pointer, "declarationId"), expected_category
        )
        if decl_error:
            diagnostics.append(decl_error)
            continue
        if event_pattern is None:
            continue
        effects = prop_spec_record.get("effects")
        effects = effects if isinstance(effects, dict) else {}
        forbidden = effects.get("forbidden", [])
        declared_events = (
            forbidden + effects.get("required", []) + effects.get("permitted", []) + effects.get("optional", [])
        )
        effect_id = effects.get("id", declaration_id)
        if event_pattern not in declared_events:
            forbidden_text = ", ".join(forbidden) if forbidden else "no events"
            diagnostics.append(
                Diagnostic(
                    "LINK_POLICY_EVENT_PATTERN_MISMATCH", path, ptr("prohibitions", index, "eventPattern"),
                    f"requested event pattern {event_pattern}, effect declaration {effect_id} forbids {forbidden_text}",
                )
            )

    return diagnostics


def _check_realization_profile(graph: Graph, path: str, profile: dict) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()
    for field in ("workloads", "costMeasures"):
        for index, item in enumerate(profile.get(field, [])):
            member_id = item.get("id")
            if member_id is None:
                continue
            if member_id in seen:
                diagnostics.append(
                    Diagnostic(
                        "LINK_DUPLICATE_PROFILE_MEMBER_ID", path, ptr(field, index, "id"),
                        f"requested local ID {member_id} in {fmt_tuple(profile)}",
                    )
                )
            else:
                seen.add(member_id)
    return diagnostics


_LINK_CHECKERS = {
    "specification": _check_specification,
    "realization": _check_realization,
    "claim": _check_claim,
    "evidence": _check_evidence,
    "consumerPolicy": _check_consumer_policy,
    "realizationProfile": _check_realization_profile,
}


def check_graph(records: dict[str, dict]) -> list[Diagnostic]:
    graph = Graph(records)
    diagnostics: list[Diagnostic] = list(graph.duplicates)
    for path in sorted(records):
        record = records[path]
        address = (record["kind"], record["id"], record["version"])
        if graph.by_address.get(address) is not record:
            continue
        checker = _LINK_CHECKERS.get(record["kind"])
        if checker is not None:
            diagnostics.extend(checker(graph, path, record))
    diagnostics.sort(key=Diagnostic.sort_key)
    return diagnostics


# ---------------------------------------------------------------------------
# Fixture-driving orchestration
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative(path: Path, base: Path) -> str:
    return str(path.relative_to(base).as_posix())


def check_flat_valid_records(schemas: SchemaRegistry) -> tuple[list[str], int]:
    errors: list[str] = []
    base = FIXTURES_DIR / "valid"
    files = sorted(p for p in base.glob("*.json"))
    records: dict[str, dict] = {}
    for path in files:
        relative = _relative(path, base)
        instance = _load_json(path)
        diagnostic = validate_record(schemas, relative, instance)
        if diagnostic:
            errors.append(f"flat valid record {relative}: unexpected schema failure {diagnostic.format()}")
            continue
        records[relative] = instance
    if len(records) != len(files):
        return errors, len(files)
    diagnostics = check_graph(records)
    for diagnostic in diagnostics:
        errors.append(f"flat valid record graph: unexpected link diagnostic {diagnostic.format()}")
    return errors, len(files)


def check_schema_invalid_fixtures(schemas: SchemaRegistry) -> tuple[list[str], int]:
    errors: list[str] = []
    count = 0
    base = FIXTURES_DIR / "invalid" / "schema"
    for kind_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        for case_path in sorted(kind_dir.glob("*.json")):
            count += 1
            expected_path = case_path.parent / (case_path.stem + ".expected.txt")
            expected = expected_path.read_text(encoding="utf-8").strip()
            instance = _load_json(case_path)
            relative = str(case_path.relative_to(FIXTURES_DIR).as_posix())
            diagnostic = validate_record(schemas, relative, instance)
            if diagnostic is None:
                errors.append(f"schema-invalid fixture {relative}: expected rejection, record validated cleanly")
                continue
            actual = f"{diagnostic.code} {diagnostic.pointer}"
            if actual != expected:
                errors.append(
                    f"schema-invalid fixture {relative}: expected '{expected}', got '{actual}'"
                )
    return errors, count


def check_link_invalid_fixtures(schemas: SchemaRegistry) -> tuple[list[str], int]:
    errors: list[str] = []
    base = FIXTURES_DIR / "invalid" / "link"
    cases = sorted(p for p in base.iterdir() if p.is_dir())
    for case_dir in cases:
        records_dir = case_dir / "records"
        expected_path = case_dir / "expected.txt"
        expected_lines = [
            line for line in expected_path.read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        records: dict[str, dict] = {}
        schema_failed = False
        for record_path in sorted(records_dir.glob("*.json")):
            relative = _relative(record_path, case_dir)
            instance = _load_json(record_path)
            diagnostic = validate_record(schemas, relative, instance)
            if diagnostic:
                errors.append(
                    f"link-invalid fixture {case_dir.name}: record {relative} unexpectedly failed schema: "
                    f"{diagnostic.format()}"
                )
                schema_failed = True
                continue
            records[relative] = instance
        if schema_failed:
            continue
        diagnostics = check_graph(records)
        actual_lines = [d.format() for d in diagnostics]
        if actual_lines != expected_lines:
            errors.append(
                f"link-invalid fixture {case_dir.name}: expected {expected_lines!r}, got {actual_lines!r}"
            )
    return errors, len(cases)


def check_link_valid_fixtures(schemas: SchemaRegistry) -> tuple[list[str], int]:
    errors: list[str] = []
    base = FIXTURES_DIR / "valid" / "link"
    cases = sorted(p for p in base.iterdir() if p.is_dir())
    for case_dir in cases:
        records_dir = case_dir / "records"
        expected_path = case_dir / "expected.txt"
        expected_count = int(expected_path.read_text(encoding="utf-8").strip())
        records: dict[str, dict] = {}
        schema_failed = False
        for record_path in sorted(records_dir.glob("*.json")):
            relative = _relative(record_path, case_dir)
            instance = _load_json(record_path)
            diagnostic = validate_record(schemas, relative, instance)
            if diagnostic:
                errors.append(
                    f"link-valid fixture {case_dir.name}: record {relative} unexpectedly failed schema: "
                    f"{diagnostic.format()}"
                )
                schema_failed = True
                continue
            records[relative] = instance
        if schema_failed:
            continue
        diagnostics = check_graph(records)
        if len(diagnostics) != expected_count:
            actual_lines = [d.format() for d in diagnostics]
            errors.append(
                f"link-valid fixture {case_dir.name}: expected {expected_count} diagnostics, "
                f"got {len(diagnostics)}: {actual_lines!r}"
            )
    return errors, len(cases)


def run_fixture_checks() -> tuple[list[str], str]:
    schemas = SchemaRegistry()
    errors: list[str] = [f"metaschema failure: {e}" for e in schemas.metaschema_errors]

    flat_errors, valid_count = check_flat_valid_records(schemas)
    errors.extend(flat_errors)

    schema_errors, schema_invalid_count = check_schema_invalid_fixtures(schemas)
    errors.extend(schema_errors)

    link_errors, link_invalid_count = check_link_invalid_fixtures(schemas)
    errors.extend(link_errors)

    link_valid_errors, link_valid_count = check_link_valid_fixtures(schemas)
    errors.extend(link_valid_errors)

    summary = (
        f"Record fixture checks passed: {valid_count} valid, {schema_invalid_count} schema-invalid, "
        f"{link_invalid_count} link-invalid, {link_valid_count} link-valid."
    )
    return errors, summary


# ---------------------------------------------------------------------------
# Direct graph-validation CLI
# ---------------------------------------------------------------------------


def _load_input(path: Path, relative: str) -> tuple[Diagnostic | None, Any]:
    """Load one direct CLI input path, turning I/O and parse failures into stable
    diagnostics instead of letting an exception surface as a traceback."""
    if not path.exists():
        return Diagnostic("INPUT_NOT_FOUND", relative, "#", f"no such file: {path}"), None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return Diagnostic("INPUT_READ_ERROR", relative, "#", str(error)), None
    try:
        return None, json.loads(text)
    except json.JSONDecodeError as error:
        return Diagnostic("INPUT_INVALID_JSON", relative, "#", str(error)), None


def validate_graph_paths(paths: list[Path]) -> list[Diagnostic]:
    schemas = SchemaRegistry()
    diagnostics: list[Diagnostic] = [Diagnostic("SCHEMA_METASCHEMA_ERROR", "#", "#", e) for e in schemas.metaschema_errors]
    records: dict[str, dict] = {}
    for path in paths:
        relative = str(path)
        input_error, instance = _load_input(path, relative)
        if input_error:
            diagnostics.append(input_error)
            continue
        diagnostic = validate_record(schemas, relative, instance)
        if diagnostic:
            diagnostics.append(diagnostic)
            continue
        records[relative] = instance
    if not diagnostics:
        diagnostics.extend(check_graph(records))
    diagnostics.sort(key=Diagnostic.sort_key)
    return diagnostics


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: record_check.py <record.json> [more.json ...]", file=sys.stderr)
        return 2
    paths = [Path(arg) for arg in argv]
    diagnostics = validate_graph_paths(paths)
    if diagnostics:
        for diagnostic in diagnostics:
            print(diagnostic.format())
        return 1
    print("Graph is valid: 0 diagnostics.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
