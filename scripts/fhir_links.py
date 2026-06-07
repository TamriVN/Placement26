#!/usr/bin/env python3
"""Build hl7.org FHIR R5 documentation URLs for resources and elements."""

from __future__ import annotations

import re

FHIR_VERSION = "R5"
FHIR_BASE = f"https://hl7.org/fhir/{FHIR_VERSION}"

# Known resources used in the VNVC mapping (PascalCase as in FHIR spec)
KNOWN_RESOURCES = {
    "Patient",
    "Immunization",
    "AdverseEvent",
    "AllergyIntolerance",
    "Condition",
    "CarePlan",
    "Encounter",
    "Location",
    "MedicationAdministration",
    "Procedure",
    "Observation",
    "RegulatedAuthorization",
    "Bundle",
    "MeasureReport",
    "Organization",
    "Medication",
    "DocumentReference",
}

# Fix known typos / shorthand from the hand-mapped spreadsheet
_ELEMENT_ALIASES = {
    "Observationbodyweight": "Observation.value[x]",
}


def _resource_slug(resource: str) -> str:
    return resource.strip().lower()


def is_fhir_resource(name: str) -> bool:
    cleaned = name.strip()
    if cleaned in KNOWN_RESOURCES:
        return True
    return bool(re.match(r"^[A-Z][A-Za-z]+$", cleaned)) and " " not in cleaned


def resource_page_url(resource: str) -> str:
    """Resource overview — structure, examples, search params."""
    return f"{FHIR_BASE}/{_resource_slug(resource)}.html"


def definitions_page_url(resource: str) -> str:
    """Detailed element table with types, cardinality, definitions."""
    return f"{FHIR_BASE}/{_resource_slug(resource)}-definitions.html"


def _normalize_element_path(resource: str, element: str) -> str:
    element = _ELEMENT_ALIASES.get(element.strip(), element.strip())
    if not element:
        return ""

    if element.startswith(f"{resource}."):
        return element

    # Spreadsheet sometimes repeats resource prefix inside element field
    if "." in element and element.split(".", 1)[0] in KNOWN_RESOURCES:
        return element

    return f"{resource}.{element}" if element else ""


def element_anchor(resource: str, element: str) -> str:
    """HTML anchor id used on hl7.org definitions pages."""
    path = _normalize_element_path(resource, element)
    if not path:
        return ""
    # Choice elements: Immunization.occurrence[x] → Immunization.occurrence_x_
    return path.replace("[x]", "_x_")


def element_definition_url(resource: str, element: str) -> str:
    """Deep link to a single element row in the definitions table."""
    anchor = element_anchor(resource, element)
    base = definitions_page_url(resource)
    return f"{base}#{anchor}" if anchor else base


def enrich_fhir_links(resource: str, element: str) -> dict[str, str]:
    """Return URL set for a mapped FHIR resource/element pair."""
    if not resource or not is_fhir_resource(resource):
        return {
            "resource_page": "",
            "definitions_page": "",
            "element_definition": "",
            "element_path": "",
        }

    path = _normalize_element_path(resource, element)
    return {
        "resource_page": resource_page_url(resource),
        "definitions_page": definitions_page_url(resource),
        "element_definition": element_definition_url(resource, element),
        "element_path": path,
    }


def link_resources_csv(resources: list[str]) -> str:
    """Not used in Python HTML — helper for tests."""
    return ", ".join(r for r in resources if is_fhir_resource(r))
