#!/usr/bin/env python3
"""Generate an example FHIR R5 Bundle — NOT sourced from docs/; illustrative only."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "example_aefi_bundle.json"

# Sample data representing a Form 2 + Form 3 follow-up with mild systemic reaction
SAMPLE = {
    "customer_id": "VNVC-2024-00123456",
    "patient_name": "Nguyen Van A",
    "gender": "male",
    "birth_date": "1990-05-15",
    "address": "123 Le Loi, District 1, Ho Chi Minh City",
    "center": "VNVC Center Quan 1",
    "vaccine_trade_name": "Qdenga",
    "vaccine_cvx": "205",  # Dengue vaccine - placeholder; confirm with formulary
    "lot_number": "ABC123",
    "expiry_date": "2026-12-31",
    "vaccination_datetime": "2026-06-01T09:30:00+07:00",
    "injection_site": "left deltoid",
    "reaction_onset": "2026-06-01T15:00:00+07:00",
    "symptoms": [
        {"code": "386661006", "display": "Fever", "system": "http://snomed.info/sct"},
        {"code": "25064002", "display": "Headache", "system": "http://snomed.info/sct"},
        {"code": "84229001", "display": "Fatigue", "system": "http://snomed.info/sct"},
    ],
    "management": "Managed at home with paracetamol",
    "outcome": "Recovered",
    "notes": "Follow-up call on day 1 post-vaccination. Patient reports mild symptoms resolving.",
}


def _uid() -> str:
    return str(uuid.uuid4())


def _ref(resource_type: str, uid: str) -> dict:
    return {"reference": f"{resource_type}/{uid}"}


def build_bundle(data: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()

    patient_id = _uid()
    location_id = _uid()
    immunization_id = _uid()
    adverse_event_id = _uid()
    encounter_id = _uid()
    careplan_id = _uid()

    patient = {
        "resourceType": "Patient",
        "id": patient_id,
        "identifier": [
            {
                "system": "urn:oid:vnvc:customer-id",
                "value": data["customer_id"],
            }
        ],
        "name": [{"text": data["patient_name"], "use": "official"}],
        "gender": data["gender"],
        "birthDate": data["birth_date"],
        "address": [{"text": data["address"], "use": "home"}],
    }

    location = {
        "resourceType": "Location",
        "id": location_id,
        "status": "active",
        "name": data["center"],
        "type": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                        "code": "PROFF",
                        "display": "Provider's Office",
                    }
                ]
            }
        ],
    }

    immunization = {
        "resourceType": "Immunization",
        "id": immunization_id,
        "status": "completed",
        "vaccineCode": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/cvx",
                    "code": data["vaccine_cvx"],
                    "display": data["vaccine_trade_name"],
                }
            ],
            "text": data["vaccine_trade_name"],
        },
        "patient": _ref("Patient", patient_id),
        "occurrenceDateTime": data["vaccination_datetime"],
        "lotNumber": data["lot_number"],
        "expirationDate": data["expiry_date"],
        "site": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                    "code": "LD",
                    "display": "Left deltoid",
                }
            ],
            "text": data["injection_site"],
        },
        "location": _ref("Location", location_id),
        "primarySource": True,
    }

    encounter = {
        "resourceType": "Encounter",
        "id": encounter_id,
        "status": "finished",
        "class": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "AMB",
                        "display": "ambulatory",
                    }
                ]
            }
        ],
        "subject": _ref("Patient", patient_id),
        "period": {"start": data["vaccination_datetime"]},
        "location": [{"location": _ref("Location", location_id)}],
    }

    adverse_event = {
        "resourceType": "AdverseEvent",
        "id": adverse_event_id,
        "status": "completed",
        "actuality": "actual",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/adverse-event-category",
                        "code": "product-problem",
                        "display": "Product Problem",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "420113004",
                    "display": "Adverse reaction to vaccine",
                }
            ]
        },
        "subject": _ref("Patient", patient_id),
        "encounter": _ref("Encounter", encounter_id),
        "effectDateTime": data["reaction_onset"],
        "recordedDate": now,
        "resultingEffect": [
            {
                "concept": {
                    "coding": [s],
                    "text": s["display"],
                }
            }
            for s in data["symptoms"]
        ],
        "location": _ref("Location", location_id),
        "seriousness": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/adverse-event-seriousness",
                    "code": "Non-serious",
                    "display": "Non-serious",
                }
            ]
        },
        "outcome": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/adverse-event-outcome",
                        "code": "resolved",
                        "display": "Resolved",
                    }
                ],
                "text": data["outcome"],
            }
        ],
        "suspectEntity": [
            {
                "instance": _ref("Immunization", immunization_id),
                "occurrenceDateTime": data["vaccination_datetime"],
            }
        ],
        "note": [{"text": data["notes"]}],
    }

    careplan = {
        "resourceType": "CarePlan",
        "id": careplan_id,
        "status": "completed",
        "intent": "plan",
        "subject": _ref("Patient", patient_id),
        "encounter": _ref("Encounter", encounter_id),
        "description": data["management"],
        "note": [{"text": data["management"]}],
    }

    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "timestamp": now,
        "identifier": {
            "system": "urn:oid:vnvc:aefi-bundle",
            "value": f"AEFI-{data['customer_id']}-{data['reaction_onset'][:10]}",
        },
        "entry": [
            {"fullUrl": f"urn:uuid:{patient_id}", "resource": patient, "request": {"method": "POST", "url": "Patient"}},
            {"fullUrl": f"urn:uuid:{location_id}", "resource": location, "request": {"method": "POST", "url": "Location"}},
            {"fullUrl": f"urn:uuid:{encounter_id}", "resource": encounter, "request": {"method": "POST", "url": "Encounter"}},
            {"fullUrl": f"urn:uuid:{immunization_id}", "resource": immunization, "request": {"method": "POST", "url": "Immunization"}},
            {"fullUrl": f"urn:uuid:{adverse_event_id}", "resource": adverse_event, "request": {"method": "POST", "url": "AdverseEvent"}},
            {"fullUrl": f"urn:uuid:{careplan_id}", "resource": careplan, "request": {"method": "POST", "url": "CarePlan"}},
        ],
    }
    return bundle


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bundle = build_bundle(SAMPLE)
    OUTPUT.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"Bundle contains {len(bundle['entry'])} resources for hospital handoff")


if __name__ == "__main__":
    main()
