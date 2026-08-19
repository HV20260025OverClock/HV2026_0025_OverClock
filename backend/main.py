import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal, Optional, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from geopy.distance import geodesic
from pydantic import BaseModel, Field

import os
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from geopy.distance import geodesic
from pydantic import BaseModel, Field


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]


# ============================================================
# LOGGING
# ============================================================

def log_event(tag: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(
        f"[{timestamp}] [{tag}] {message}",
        flush=True,
    )


# ============================================================
# SUPABASE
# ============================================================

supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client

        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )

        log_event(
            "DATABASE",
            "Supabase client initialized.",
        )

    except Exception as exc:
        log_event(
            "DATABASE",
            f"Supabase initialization failed: {exc}",
        )

else:
    log_event(
        "DATABASE",
        "SUPABASE_URL or SUPABASE_KEY is missing.",
    )


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="RedAid Emergency Dispatch Core",
    version="3.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# TYPES
# ============================================================

BloodGroup = Literal[
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
]

UrgencyLevel = Literal[
    "critical",
    "high",
    "medium",
]


class EmergencyRequestCreate(BaseModel):
    blood_group: BloodGroup

    units_required: int = Field(
        ...,
        ge=1,
        le=20,
    )

    urgency: UrgencyLevel

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
    )

    hospital_name: Optional[str] = None


class DonorResponseRequest(BaseModel):
    donor_id: str
    action: Literal[
        "accept",
        "reject",
    ]


class AvailabilityUpdate(BaseModel):
    is_available: bool


# ============================================================
# BLOOD COMPATIBILITY
# ============================================================

COMPATIBLE_DONOR_GROUPS = {

    "A+": [
        "A+",
        "A-",
        "O+",
        "O-",
    ],

    "A-": [
        "A-",
        "O-",
    ],

    "B+": [
        "B+",
        "B-",
        "O+",
        "O-",
    ],

    "B-": [
        "B-",
        "O-",
    ],

    "AB+": [
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
    ],

    "AB-": [
        "A-",
        "B-",
        "AB-",
        "O-",
    ],

    "O+": [
        "O+",
        "O-",
    ],

    "O-": [
        "O-",
    ],
}


# ============================================================
# REQUEST TICKET ID
# ============================================================

REQUEST_NAMESPACE = uuid.UUID(
    "8f6d4e30-3b4a-4d9f-9e77-5c6d7a8b9c10"
)


def create_ticket_id() -> str:
    return (
        "REQ-"
        + uuid.uuid4().hex[:6].upper()
    )


def ticket_to_uuid(ticket_id: str) -> str:
    """
    Converts our human-readable REQ-XXXXXX
    into a deterministic UUID for Supabase.
    """

    return str(
        uuid.uuid5(
            REQUEST_NAMESPACE,
            ticket_id,
        )
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def health_check():

    return {
        "status": "online",
        "service": "RedAid Emergency Dispatch Core",
        "database": (
            "connected"
            if supabase
            else "not connected"
        ),
    }


# ============================================================
# DEBUG: CHECK HOSPITALS
# ============================================================

@app.get("/debug/hospitals")
def debug_hospitals():

    if not supabase:
        return {
            "error":
                "Supabase client is not initialized"
        }

    try:

        result = (
            supabase
            .table("hospitals")
            .select(
                "id,user_id,hospital_name,"
                "latitude,longitude,is_verified"
            )
            .execute()
        )

        hospitals = result.data or []

        print(
            f"[DEBUG] Supabase returned "
            f"{len(hospitals)} hospital(s)",
            flush=True,
        )

        print(
            f"[DEBUG] Hospitals: {hospitals}",
            flush=True,
        )

        return {
            "count": len(hospitals),
            "hospitals": hospitals,
        }

    except Exception as exc:

        print(
            f"[DEBUG] Hospital query failed: {exc}",
            flush=True,
        )

        return {
            "error": str(exc),
        }


# ============================================================
# HOSPITAL LOOKUP
# ============================================================

def get_hospital(
    hospital_name: str,
) -> dict:

    if not supabase:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected.",
        )

    clean_name = hospital_name.strip()

    try:

        # First retrieve hospitals without a filter.
        # This makes debugging much easier.
        response = (
            supabase
            .table("hospitals")
            .select(
                "id,user_id,hospital_name,"
                "latitude,longitude,is_verified"
            )
            .execute()
        )

        hospitals = response.data or []

        log_event(
            "HOSPITAL",
            (
                f"Supabase returned "
                f"{len(hospitals)} hospital(s)"
            ),
        )

        # Find hospital ourselves.
        requested = clean_name.lower()

        for hospital in hospitals:

            database_name = str(
                hospital.get(
                    "hospital_name",
                    "",
                )
            ).strip().lower()

            if (
                database_name == requested
                or requested in database_name
                or database_name in requested
            ):

                log_event(
                    "HOSPITAL",
                    (
                        "MATCH FOUND: "
                        f"{hospital.get('hospital_name')}"
                    ),
                )

                return hospital

        # Helpful error rather than vague "not found"
        visible_names = [
            h.get("hospital_name")
            for h in hospitals
        ]

        raise HTTPException(
            status_code=404,
            detail={
                "message": (
                    f"Hospital '{clean_name}' "
                    "was not found."
                ),
                "hospitals_visible_to_fastapi":
                    visible_names,
            },
        )

    except HTTPException:
        raise

    except Exception as exc:

        log_event(
            "DATABASE",
            f"Hospital lookup failed: {exc}",
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Hospital lookup failed: "
                f"{exc}"
            ),
        )


# ============================================================
# LOAD DONORS
# ============================================================

def load_available_donors(
    blood_group: str,
) -> list:

    if not supabase:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected.",
        )

    compatible_groups = (
        COMPATIBLE_DONOR_GROUPS.get(
            blood_group,
            [blood_group],
        )
    )

    try:

        response = (
            supabase
            .table("donors")
            .select("*")
            .eq(
                "is_available",
                True,
            )
            .in_(
                "blood_type",
                compatible_groups,
            )
            .execute()
        )

        donors = response.data or []

        log_event(
            "DATABASE",
            (
                f"Loaded {len(donors)} "
                "available compatible donor(s)"
            ),
        )

        return donors

    except Exception as exc:

        log_event(
            "DATABASE",
            f"Donor query failed: {exc}",
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load donors: "
                f"{exc}"
            ),
        )


# ============================================================
# PRIORITY SCORE
# ============================================================

def calculate_priority_score(
    distance_km: float,
    exact_match: bool,
    response_rate: float = 0,
) -> float:

    distance_score = max(
        0,
        100 - distance_km * 6,
    )

    distance_component = (
        distance_score * 0.60
    )

    compatibility_component = (
        100 if exact_match else 78
    ) * 0.30

    reliability_component = (
        max(
            0,
            min(
                100,
                float(response_rate or 0),
            ),
        )
        * 0.10
    )

    score = (
        distance_component
        + compatibility_component
        + reliability_component
    )

    return round(
        min(
            98.5,
            max(
                15,
                score,
            ),
        ),
        1,
    )


# ============================================================
# FIND MATCHES
# ============================================================

def find_donor_matches(
    latitude: float,
    longitude: float,
    blood_group: str,
    radius_km: float,
) -> list:

    donors = load_available_donors(
        blood_group
    )

    matches = []

    for donor in donors:

        donor_lat = donor.get(
            "latitude"
        )

        donor_lon = donor.get(
            "longitude"
        )

        if (
            donor_lat is None
            or donor_lon is None
        ):
            continue

        distance = geodesic(
            (
                latitude,
                longitude,
            ),
            (
                float(donor_lat),
                float(donor_lon),
            ),
        ).km

        distance = round(
            distance,
            2,
        )

        if distance > radius_km:
            continue

        donor_blood = donor.get(
            "blood_type"
        )

        exact_match = (
            donor_blood == blood_group
        )

        response_rate = donor.get(
            "response_rate",
            0,
        )

        score = calculate_priority_score(
            distance_km=distance,
            exact_match=exact_match,
            response_rate=response_rate,
        )

        matches.append(
            {
                "donor_id": str(
                    donor.get("id")
                ),

                "name": donor.get(
                    "name",
                    "Registered Donor",
                ),

                "blood_group": donor_blood,

                "is_exact_match":
                    exact_match,

                "distance_km":
                    distance,

                "priority_score":
                    score,

                "status":
                    "notified",
            }
        )

    matches.sort(
        key=lambda donor:
            donor["priority_score"],
        reverse=True,
    )

    log_event(
        "MATCH_ENGINE",
        (
            f"{len(matches)} donor(s) "
            f"mapped within {radius_km} km"
        ),
    )

    return matches


# ============================================================
# SAVE MATCHES
# ============================================================

def save_donor_matches(
    request_uuid: str,
    matches: list,
):

    if not supabase:
        return

    for match in matches:

        donor_id = match["donor_id"]

        try:

            # Don't create duplicate responses.
            existing = (
                supabase
                .table("donor_responses")
                .select("id")
                .eq(
                    "request_id",
                    request_uuid,
                )
                .eq(
                    "donor_id",
                    donor_id,
                )
                .limit(1)
                .execute()
            )

            if existing.data:
                continue

            response_data = {

                "request_id":
                    request_uuid,

                "donor_id":
                    donor_id,

                "response_status":
                    "notified",

                "distance_km":
                    match["distance_km"],

                "match_score":
                    match["priority_score"],
            }

            (
                supabase
                .table("donor_responses")
                .insert(response_data)
                .execute()
            )

            log_event(
                "MATCH",
                (
                    f"Saved match "
                    f"{donor_id} → "
                    f"{request_uuid}"
                ),
            )

        except Exception as exc:

            log_event(
                "DATABASE",
                (
                    f"Could not save match "
                    f"{donor_id}: {exc}"
                ),
            )


# ============================================================
# GET REQUEST
# ============================================================

def get_request_from_database(
    request_id: str,
) -> dict:

    if not supabase:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected.",
        )

    if request_id.startswith("REQ-"):
        database_id = ticket_to_uuid(
            request_id
        )
    else:
        database_id = request_id

    try:

        response = (
            supabase
            .table("blood_requests")
            .select("*")
            .eq(
                "id",
                database_id,
            )
            .limit(1)
            .execute()
        )

        if not response.data:

            raise HTTPException(
                status_code=404,
                detail="Request not found.",
            )

        request = response.data[0]

        request["_ticket_id"] = request_id

        return request

    except HTTPException:
        raise

    except Exception as exc:

        log_event(
            "DATABASE",
            f"Request lookup failed: {exc}",
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load request: "
                f"{exc}"
            ),
        )


# ============================================================
# CREATE EMERGENCY REQUEST
# ============================================================

@app.post(
    "/requests",
    status_code=201,
)
def create_emergency_request(
    payload: EmergencyRequestCreate,
):

    if not supabase:

        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected.",
        )

    hospital_name = (
        payload.hospital_name
        or "RedAid Test Hospital"
    )

    # --------------------------------------------------------
    # 1. Find hospital
    # --------------------------------------------------------

    hospital = get_hospital(
        hospital_name
    )

    hospital_id = hospital["id"]
    requester_id = hospital["user_id"]

    # --------------------------------------------------------
    # 2. Generate IDs
    # --------------------------------------------------------

    ticket_id = create_ticket_id()

    database_id = ticket_to_uuid(
        ticket_id
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    # --------------------------------------------------------
    # 3. Insert into blood_requests
    # --------------------------------------------------------

    request_data = {

        "id":
            database_id,

        "requester_id":
            requester_id,

        "hospital_id":
            hospital_id,

        "blood_type":
            payload.blood_group,

        "units_needed":
            payload.units_required,

        "units_fulfilled":
            0,

        "urgency":
            payload.urgency,

        "status":
            "open",

        "current_radius_km":
            5,

        "created_at":
            now,

        "updated_at":
            now,
    }

    try:

        response = (
            supabase
            .table("blood_requests")
            .insert(request_data)
            .select("*")
            .execute()
        )

        if not response.data:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Supabase did not return "
                    "the inserted request."
                ),
            )

        saved_request = response.data[0]

    except HTTPException:
        raise

    except Exception as exc:

        log_event(
            "DATABASE",
            f"Insert failed: {exc}",
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save request to "
                f"Supabase: {exc}"
            ),
        )

    # --------------------------------------------------------
    # 4. Find donors
    # --------------------------------------------------------

    matches = find_donor_matches(
        latitude=float(
            hospital["latitude"]
        ),
        longitude=float(
            hospital["longitude"]
        ),
        blood_group=
            payload.blood_group,
        radius_km=15,
    )

    # --------------------------------------------------------
    # 5. Save donor matches
    # --------------------------------------------------------

    save_donor_matches(
        request_uuid=database_id,
        matches=matches,
    )

    log_event(
        "EMERGENCY",
        (
            f"Ticket {ticket_id} created | "
            f"DB ID {database_id} | "
            f"{payload.blood_group} | "
            f"{payload.units_required} units | "
            f"{hospital_name} | "
            f"{len(matches)} donor(s)"
        ),
    )

    # --------------------------------------------------------
    # 6. Return to React
    # --------------------------------------------------------

    return {

        "id":
            ticket_id,

        "database_id":
            database_id,

        "requester_id":
            requester_id,

        "hospital_id":
            hospital_id,

        "hospital_name":
            hospital_name,

        "blood_group":
            payload.blood_group,

        "units_required":
            payload.units_required,

        "urgency":
            payload.urgency,

        "status":
            "open",

        "match_count":
            len(matches),

        "matches":
            matches,

        "created_at":
            saved_request.get(
                "created_at",
                now,
            ),
    }


# ============================================================
# LIST REQUESTS
# ============================================================

@app.get("/requests")
def list_requests():

    if not supabase:

        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected.",
        )

    try:

        response = (
            supabase
            .table("blood_requests")
            .select("*")
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return response.data or []

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load requests: "
                f"{exc}"
            ),
        )


# ============================================================
# GET REQUEST
# ============================================================

@app.get(
    "/requests/{request_id}"
)
def get_request(
    request_id: str,
):

    return get_request_from_database(
        request_id
    )


# ============================================================
# GET MATCHES
# ============================================================

@app.get(
    "/requests/{request_id}/matches"
)
def get_matches(
    request_id: str,

    radius_km: float = Query(
        15,
        ge=1,
        le=100,
    ),
):

    request = get_request_from_database(
        request_id
    )

    database_id = request["id"]

    hospital_id = request[
        "hospital_id"
    ]

    try:

        hospital_response = (
            supabase
            .table("hospitals")
            .select(
                "id,hospital_name,"
                "latitude,longitude"
            )
            .eq(
                "id",
                hospital_id,
            )
            .limit(1)
            .execute()
        )

        if not hospital_response.data:

            raise HTTPException(
                status_code=404,
                detail="Hospital not found.",
            )

        hospital = (
            hospital_response.data[0]
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load hospital: "
                f"{exc}"
            ),
        )

    matches = find_donor_matches(
        latitude=float(
            hospital["latitude"]
        ),
        longitude=float(
            hospital["longitude"]
        ),
        blood_group=request[
            "blood_type"
        ],
        radius_km=radius_km,
    )

    save_donor_matches(
        request_uuid=database_id,
        matches=matches,
    )

    return {

        "request_id":
            request_id,

        "database_request_id":
            database_id,

        "blood_group":
            request["blood_type"],

        "radius_km":
            radius_km,

        "match_count":
            len(matches),

        "matches":
            matches,
    }


# ============================================================
# DONOR RESPONSE
# ============================================================

@app.post(
    "/requests/{request_id}/respond"
)
def respond_to_request(
    request_id: str,
    payload: DonorResponseRequest,
):

    request = get_request_from_database(
        request_id
    )

    database_id = request["id"]

    try:

        donor = (
            supabase
            .table("donors")
            .select("id,name")
            .eq(
                "id",
                payload.donor_id,
            )
            .limit(1)
            .execute()
        )

        if not donor.data:

            raise HTTPException(
                status_code=404,
                detail="Donor not found.",
            )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not find donor: "
                f"{exc}"
            ),
        )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    if payload.action == "accept":

        try:

            (
                supabase
                .table("donor_responses")
                .update(
                    {
                        "response_status":
                            "accepted",

                        "responded_at":
                            now,

                        "accepted_at":
                            now,

                        "updated_at":
                            now,
                    }
                )
                .eq(
                    "request_id",
                    database_id,
                )
                .eq(
                    "donor_id",
                    payload.donor_id,
                )
                .execute()
            )

            current_units = int(
                request.get(
                    "units_fulfilled",
                    0,
                )
                or 0
            )

            required_units = int(
                request.get(
                    "units_needed",
                    1,
                )
            )

            fulfilled_units = (
                current_units + 1
            )

            if (
                fulfilled_units
                >= required_units
            ):
                new_status = "fulfilled"

            else:
                new_status = (
                    "partially_fulfilled"
                )

            (
                supabase
                .table("blood_requests")
                .update(
                    {
                        "units_fulfilled":
                            fulfilled_units,

                        "status":
                            new_status,

                        "updated_at":
                            now,
                    }
                )
                .eq(
                    "id",
                    database_id,
                )
                .execute()
            )

            return {

                "request_id":
                    request_id,

                "donor_id":
                    payload.donor_id,

                "action":
                    "accept",

                "status":
                    new_status,

                "units_fulfilled":
                    fulfilled_units,

                "units_required":
                    required_units,
            }

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not save donor "
                    f"acceptance: {exc}"
                ),
            )

    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

    try:

        (
            supabase
            .table("donor_responses")
            .update(
                {
                    "response_status":
                        "declined",

                    "responded_at":
                        now,

                    "updated_at":
                        now,
                }
            )
            .eq(
                "request_id",
                database_id,
            )
            .eq(
                "donor_id",
                payload.donor_id,
            )
            .execute()
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not save donor "
                f"rejection: {exc}"
            ),
        )

    return {

        "request_id":
            request_id,

        "donor_id":
            payload.donor_id,

        "action":
            "reject",

        "status":
            "declined",
    }


# ============================================================
# DONOR PROFILE
# ============================================================

@app.get(
    "/donors/{donor_id}"
)
def get_donor_profile(
    donor_id: str,
):

    if not supabase:

        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected.",
        )

    try:

        response = (
            supabase
            .table("donors")
            .select("*")
            .eq(
                "id",
                donor_id,
            )
            .limit(1)
            .execute()
        )

        if not response.data:

            raise HTTPException(
                status_code=404,
                detail="Donor not found.",
            )

        return response.data[0]

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load donor: "
                f"{exc}"
            ),
        )


# ============================================================
# DONOR AVAILABILITY
# ============================================================

@app.patch(
    "/donors/{donor_id}/availability"
)
def update_donor_availability(
    donor_id: str,
    payload: AvailabilityUpdate,
):

    if not supabase:

        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected.",
        )

    try:

        response = (
            supabase
            .table("donors")
            .update(
                {
                    "is_available":
                        payload.is_available
                }
            )
            .eq(
                "id",
                donor_id,
            )
            .execute()
        )

        if not response.data:

            raise HTTPException(
                status_code=404,
                detail="Donor not found.",
            )

        return {

            "donor_id":
                donor_id,

            "is_available":
                payload.is_available,
        }

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not update availability: "
                f"{exc}"
            ),
        )


# ============================================================
# DONOR REQUESTS
# ============================================================

@app.get(
    "/donors/{donor_id}/requests"
)
def get_donor_requests(
    donor_id: str,
):

    if not supabase:

        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected.",
        )

    try:

        response = (
            supabase
            .table("donor_responses")
            .select(
                "id,request_id,"
                "notified_at,response_status,"
                "distance_km,match_score"
            )
            .eq(
                "donor_id",
                donor_id,
            )
            .order(
                "created_at",
                desc=True,
            )
            .execute()
        )

        return response.data or []

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load donor requests: "
                f"{exc}"
            ),
        )
# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in raw_origins.split(",")
    if origin.strip()
]


# ============================================================
# LOGGING
# ============================================================

def log_event(tag: str, message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(
        f"\033[94m[{timestamp}]\033[0m "
        f"\033[92m[{tag}]\033[0m "
        f"{message}",
        flush=True,
    )


# ============================================================
# SUPABASE
# ============================================================

supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import Client, create_client

        supabase: Client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY,
        )

        log_event(
            "DATABASE",
            "Connected to Supabase PostgreSQL cluster.",
        )

    except Exception as exc:
        log_event(
            "DATABASE",
            f"Supabase connection failed: {exc}. "
            "Using in-memory mode.",
        )

else:
    log_event(
        "DATABASE",
        "SUPABASE_URL/SUPABASE_KEY not configured. "
        "Using in-memory demo mode.",
    )


# ============================================================
# ESCALATION CONFIGURATION
# ============================================================

ESCALATION_TIERS = [
    {
        "tier": 1,
        "radius_km": 5.0,
        "wait_seconds": 90,
    },
    {
        "tier": 2,
        "radius_km": 10.0,
        "wait_seconds": 90,
    },
    {
        "tier": 3,
        "radius_km": 20.0,
        "wait_seconds": 90,
    },
]

BACKGROUND_LOOP_INTERVAL_SECONDS = 5


# ============================================================
# DEMO DATA
# ============================================================

mock_donors = [
    {
        "id": "DNR-8402",
        "name": "Karthik Reddy",
        "blood_group": "O+",
        "phone": "+91 98765 43210",
        "last_donation_date": "2026-04-01T00:00:00+00:00",
        "latitude": 17.4280,
        "longitude": 78.4180,
        "is_available": True,
        "total_donations": 5,
    },
    {
        "id": "DNR-9120",
        "name": "Ananya Sharma",
        "blood_group": "O-",
        "phone": "+91 98765 43211",
        "last_donation_date": "2026-03-15T00:00:00+00:00",
        "latitude": 17.4190,
        "longitude": 78.4050,
        "is_available": True,
        "total_donations": 8,
    },
    {
        "id": "DNR-5521",
        "name": "Syed Imran",
        "blood_group": "O+",
        "phone": "+91 98765 43212",
        "last_donation_date": "2026-05-01T00:00:00+00:00",
        "latitude": 17.4450,
        "longitude": 78.4300,
        "is_available": True,
        "total_donations": 3,
    },
    {
        "id": "DNR-2309",
        "name": "Pooja Sharma",
        "blood_group": "A+",
        "phone": "+91 98765 43213",
        "last_donation_date": "2026-02-01T00:00:00+00:00",
        "latitude": 17.4214,
        "longitude": 78.4552,
        "is_available": True,
        "total_donations": 2,
    },
    {
        "id": "DNR-1044",
        "name": "Rahul Verma",
        "blood_group": "O+",
        "phone": "+91 98765 43214",
        "last_donation_date": "2026-04-01T00:00:00+00:00",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "is_available": False,
        "total_donations": 1,
    },
]


mock_blood_banks = [
    {
        "id": "BB-001",
        "name": "Red Cross Blood Bank, Nampally",
        "latitude": 17.3937,
        "longitude": 78.4738,
        "phone": "040-2320-1234",
    },
    {
        "id": "BB-002",
        "name": "Government Blood Bank, Koti",
        "latitude": 17.3833,
        "longitude": 78.4772,
        "phone": "040-2461-5678",
    },
    {
        "id": "BB-003",
        "name": "Sri Sathya Sai Blood Bank, Hitech City",
        "latitude": 17.4483,
        "longitude": 78.3915,
        "phone": "040-4020-9911",
    },
]


mock_requests = {}

donor_notifications: dict[str, list[dict]] = {}


# ============================================================
# GLOBAL TYPES
# ============================================================

BloodGroup = Literal[
    "A+",
    "A-",
    "B+",
    "B-",
    "AB+",
    "AB-",
    "O+",
    "O-",
]

UrgencyLevel = Literal[
    "critical",
    "high",
    "medium",
]

DonorAction = Literal[
    "accept",
    "reject",
]

RequestStatus = Literal[
    "searching",
    "partially_fulfilled",
    "fulfilled",
    "escalated_to_blood_bank",
    "closed",
    "cancelled",
]


# ============================================================
# PYDANTIC MODELS
# ============================================================

class EmergencyRequestCreate(BaseModel):
    blood_group: BloodGroup

    units_required: int = Field(
        ...,
        ge=1,
        le=20,
    )

    urgency: UrgencyLevel

    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
    )

    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
    )

    hospital_name: Optional[str] = Field(
        default="Apollo Hospitals, Jubilee Hills"
    )


class DonorResponse(BaseModel):
    donor_id: str = Field(
        ...,
        min_length=1,
    )

    action: DonorAction


class AvailabilityUpdate(BaseModel):
    is_available: bool


# ============================================================
# BIOLOGICAL COMPATIBILITY
# ============================================================

RED_CELL_DONOR_COMPATIBILITY = {
    "A+": ["A+", "A-", "O+", "O-"],
    "A-": ["A-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "AB+": [
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
    ],
    "AB-": [
        "A-",
        "B-",
        "AB-",
        "O-",
    ],
    "O+": ["O+", "O-"],
    "O-": ["O-"],
}


# ============================================================
# PRIORITY SCORE
# ============================================================

def compute_priority_score(
    distance_km: float,
    is_exact_match: bool,
    total_donations: int = 0,
) -> float:

    proximity_factor = (
        max(
            0.0,
            100.0 - (distance_km * 6.0),
        )
        * 0.60
    )

    compatibility_factor = (
        100.0 if is_exact_match else 78.0
    ) * 0.30

    reliability_factor = (
        min(
            100.0,
            70.0 + min(total_donations, 6) * 5.0,
        )
        * 0.10
    )

    total_score = (
        proximity_factor
        + compatibility_factor
        + reliability_factor
    )

    return round(
        min(
            98.5,
            max(15.0, total_score),
        ),
        1,
    )


# ============================================================
# COORDINATES
# ============================================================

def get_donor_coordinates(
    donor: dict,
) -> Tuple[
    Optional[float],
    Optional[float],
]:

    lat = (
        donor.get("latitude")
        if donor.get("latitude") is not None
        else donor.get("lat")
    )

    lon = (
        donor.get("longitude")
        if donor.get("longitude") is not None
        else donor.get("lon")
    )

    return lat, lon


# ============================================================
# LOAD DONORS
# ============================================================

def load_available_donors(
    compatible_groups: list[str],
) -> list[dict]:

    if supabase:
        try:
            response = (
                supabase
                .table("donors")
                .select("*")
                .eq("is_available", True)
                .in_("blood_group", compatible_groups)
                .execute()
            )

            return response.data or []

        except Exception as exc:
            log_event(
                "DATABASE",
                f"Donor query failed: {exc}. "
                "Using fallback memory.",
            )

    return [
        donor
        for donor in mock_donors
        if donor.get("is_available") is True
        and donor.get("blood_group")
        in compatible_groups
    ]


# ============================================================
# FIND DONOR MATCHES
# ============================================================

def find_donor_matches(
    request_latitude: float,
    request_longitude: float,
    requested_blood_group: str,
    max_radius_km: float = 15.0,
    exclude_donor_ids: Optional[set] = None,
) -> list[dict]:

    exclude_donor_ids = (
        exclude_donor_ids or set()
    )

    compatible_groups = (
        RED_CELL_DONOR_COMPATIBILITY.get(
            requested_blood_group,
            [requested_blood_group],
        )
    )

    donors = load_available_donors(
        compatible_groups
    )

    ranked_matches = []

    for donor in donors:

        donor_id = str(
            donor.get("id")
        )

        if donor_id in exclude_donor_ids:
            continue

        donor_lat, donor_lon = (
            get_donor_coordinates(donor)
        )

        if donor_lat is None or donor_lon is None:
            continue

        distance_km = round(
            geodesic(
                (
                    request_latitude,
                    request_longitude,
                ),
                (
                    donor_lat,
                    donor_lon,
                ),
            ).km,
            2,
        )

        if distance_km > max_radius_km:
            continue

        is_exact = (
            donor.get("blood_group")
            == requested_blood_group
        )

        donations_count = donor.get(
            "total_donations",
            1,
        )

        score = compute_priority_score(
            distance_km,
            is_exact,
            donations_count,
        )

        ranked_matches.append(
            {
                "donor_id": donor_id,
                "name": donor.get(
                    "name",
                    "Registered Donor",
                ),
                "blood_group": donor.get(
                    "blood_group"
                ),
                "is_exact_match": is_exact,
                "distance_km": distance_km,
                "priority_score": score,
                "status": "notified",
            }
        )

    ranked_matches.sort(
        key=lambda x: x["priority_score"],
        reverse=True,
    )

    return ranked_matches


# ============================================================
# BLOOD BANK MATCHING
# ============================================================

def find_nearby_blood_banks(
    latitude: float,
    longitude: float,
    max_radius_km: float = 25.0,
) -> list[dict]:

    ranked = []

    for bank in mock_blood_banks:

        distance_km = round(
            geodesic(
                (
                    latitude,
                    longitude,
                ),
                (
                    bank["latitude"],
                    bank["longitude"],
                ),
            ).km,
            2,
        )

        if distance_km > max_radius_km:
            continue

        ranked.append(
            {
                **bank,
                "distance_km": distance_km,
            }
        )

    ranked.sort(
        key=lambda x: x["distance_km"]
    )

    return ranked


# ============================================================
# NOTIFICATIONS
# ============================================================

def notify_donor(
    donor_id: str,
    donor_name: str,
    request_id: str,
    blood_group: str,
    hospital_name: str = "",
    urgency: str = "",
    distance_km: Optional[float] = None,
) -> None:

    log_event(
        "NOTIFY",
        f"-> {donor_name} ({donor_id}): "
        f"urgent {blood_group} request "
        f"{request_id} near you",
    )

    notification = {
        "id": f"NOTIF-{uuid.uuid4().hex[:8]}",
        "donor_id": donor_id,
        "request_id": request_id,
        "blood_group": blood_group,
        "hospital_name": hospital_name,
        "urgency": urgency,
        "distance_km": distance_km,
        "status": "pending",
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    donor_notifications.setdefault(
        donor_id,
        [],
    ).append(notification)


def mark_notifications_responded(
    donor_id: str,
    request_id: str,
) -> None:

    for note in donor_notifications.get(
        donor_id,
        [],
    ):

        if (
            note["request_id"] == request_id
            and note["status"] == "pending"
        ):
            note["status"] = "responded"


# ============================================================
# STORAGE
# ============================================================

def get_request_from_storage(
    request_id: str,
) -> dict:

    if supabase:
        try:
            res = (
                supabase
                .table("blood_requests")
                .select("*")
                .eq("id", request_id)
                .execute()
            )

            if res.data:
                return res.data[0]

        except Exception as exc:
            log_event(
                "DATABASE",
                f"Fetch failed: {exc}. "
                "Checking fallback cache.",
            )

    if request_id in mock_requests:
        return mock_requests[request_id]

    raise HTTPException(
        status_code=404,
        detail="Emergency request ticket not found.",
    )


def save_request(
    request_data: dict,
) -> dict:

    if supabase:
        try:
            res = (
                supabase
                .table("blood_requests")
                .insert(request_data)
                .execute()
            )

            if res.data:
                return res.data[0]

        except Exception as exc:
            log_event(
                "DATABASE",
                f"Insert failed: {exc}. "
                "Persisting to local memory.",
            )

    mock_requests[
        request_data["id"]
    ] = request_data

    return request_data


def update_request(
    request_id: str,
    update_payload: dict,
) -> None:

    if supabase:
        try:
            (
                supabase
                .table("blood_requests")
                .update(update_payload)
                .eq("id", request_id)
                .execute()
            )

        except Exception as exc:
            log_event(
                "DATABASE",
                f"Update failed: {exc}",
            )

    if request_id in mock_requests:
        mock_requests[
            request_id
        ].update(update_payload)


def list_active_requests() -> list[dict]:

    if supabase:
        try:
            res = (
                supabase
                .table("blood_requests")
                .select("*")
                .in_(
                    "status",
                    [
                        "searching",
                        "partially_fulfilled",
                    ],
                )
                .execute()
            )

            return res.data or []

        except Exception as exc:
            log_event(
                "DATABASE",
                f"Active request query failed: {exc}",
            )

            return []

    return [
        r
        for r in mock_requests.values()
        if r.get("status")
        in {
            "searching",
            "partially_fulfilled",
        }
    ]


# ============================================================
# ESCALATION
# ============================================================

def seconds_since(
    iso_timestamp: str,
) -> float:

    then = datetime.fromisoformat(
        iso_timestamp
    )

    return (
        datetime.now(timezone.utc)
        - then
    ).total_seconds()


def run_tier_for_request(
    req: dict,
) -> None:

    tier_index = (
        req.get("current_tier", 1) - 1
    )

    tier_started_at = (
        req.get("tier_started_at")
        or req["created_at"]
    )

    if seconds_since(
        tier_started_at
    ) < ESCALATION_TIERS[
        tier_index
    ]["wait_seconds"]:

        return

    already_notified = set(
        req.get(
            "notified_donor_ids",
            [],
        )
    )

    next_tier_index = (
        tier_index + 1
    )

    if (
        next_tier_index
        >= len(ESCALATION_TIERS)
    ):

        banks = find_nearby_blood_banks(
            req["latitude"],
            req["longitude"],
        )

        update_request(
            req["id"],
            {
                "status":
                    "escalated_to_blood_bank",
                "nearby_blood_banks": banks,
            },
        )

        log_event(
            "ESCALATION",
            f"{req['id']}: all donor tiers exhausted "
            f"-> escalated to {len(banks)} blood bank(s)",
        )

        return

    next_tier = ESCALATION_TIERS[
        next_tier_index
    ]

    new_matches = find_donor_matches(
        request_latitude=req["latitude"],
        request_longitude=req["longitude"],
        requested_blood_group=req["blood_group"],
        max_radius_km=next_tier["radius_km"],
        exclude_donor_ids=already_notified,
    )

    for match in new_matches:

        notify_donor(
            match["donor_id"],
            match["name"],
            req["id"],
            req["blood_group"],
            hospital_name=req.get(
                "hospital_name",
                "",
            ),
            urgency=req.get(
                "urgency",
                "",
            ),
            distance_km=match[
                "distance_km"
            ],
        )

        already_notified.add(
            match["donor_id"]
        )

    update_request(
        req["id"],
        {
            "current_tier":
                next_tier["tier"],
            "tier_started_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
            "notified_donor_ids":
                list(already_notified),
        },
    )

    log_event(
        "ESCALATION",
        f"{req['id']}: advanced to "
        f"tier {next_tier['tier']} "
        f"(radius {next_tier['radius_km']}km), "
        f"notified {len(new_matches)} new donor(s)",
    )


async def escalation_background_loop() -> None:

    while True:

        try:

            for req in list_active_requests():
                run_tier_for_request(req)

        except Exception as exc:

            log_event(
                "ESCALATION_LOOP",
                f"Sweep error: {exc}",
            )

        await asyncio.sleep(
            BACKGROUND_LOOP_INTERVAL_SECONDS
        )


# ============================================================
# FASTAPI APPLICATION
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    task = asyncio.create_task(
        escalation_background_loop()
    )

    log_event(
        "STARTUP",
        "Escalation background loop started.",
    )

    yield

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="RedAid Emergency Dispatch Core",
    version="3.0.0",
    description=(
        "Location-aware emergency blood donor "
        "discovery, tiered escalation, and "
        "blood bank fallback engine."
    ),
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def health_check():

    return {
        "status": "online",
        "service":
            "RedAid Emergency Dispatch Core",
        "storage":
            "supabase-postgres"
            if supabase
            else "in-memory-demo",
        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }


# ============================================================
# DONOR PROFILE
# ============================================================

@app.get("/donors/{donor_id}")
def get_donor_profile(
    donor_id: str,
):

    # Supabase
    if supabase:

        try:

            res = (
                supabase
                .table("donors")
                .select("*")
                .eq("id", donor_id)
                .execute()
            )

            if res.data:
                return res.data[0]

        except Exception as exc:

            log_event(
                "DATABASE",
                f"Donor profile fetch failed: {exc}",
            )

    # Demo fallback
    for donor in mock_donors:

        if donor["id"] == donor_id:
            return donor

    raise HTTPException(
        status_code=404,
        detail="Donor profile not found.",
    )


# ============================================================
# DONOR REQUESTS
# ============================================================

@app.get("/donors/{donor_id}/requests")
def get_donor_requests(
    donor_id: str,
):

    # Verify donor
    donor_exists = False

    for donor in mock_donors:

        if donor["id"] == donor_id:
            donor_exists = True
            break

    if supabase:

        try:

            donor_check = (
                supabase
                .table("donors")
                .select("id")
                .eq("id", donor_id)
                .execute()
            )

            if donor_check.data:
                donor_exists = True

        except Exception as exc:

            log_event(
                "DATABASE",
                f"Donor verification failed: {exc}",
            )

    if not donor_exists:

        raise HTTPException(
            status_code=404,
            detail="Donor not found.",
        )

    # Supabase requests
    if supabase:

        try:

            res = (
                supabase
                .table("blood_requests")
                .select("*")
                .in_(
                    "status",
                    [
                        "searching",
                        "partially_fulfilled",
                    ],
                )
                .order(
                    "created_at",
                    desc=True,
                )
                .execute()
            )

            requests = res.data or []

        except Exception as exc:

            log_event(
                "DATABASE",
                f"Request fetch failed: {exc}",
            )

            requests = []

    # Memory requests
    else:

        requests = [
            r
            for r in mock_requests.values()
            if r.get("status")
            in {
                "searching",
                "partially_fulfilled",
            }
        ]

    return requests


# ============================================================
# CREATE EMERGENCY REQUEST
# ============================================================

@app.post(
    "/requests",
    status_code=201,
)
def create_emergency_request(
    payload: EmergencyRequestCreate,
):

    request_id = (
        f"REQ-{uuid.uuid4().hex[:6].upper()}"
    )

    hospital = (
        payload.hospital_name
        or "Apollo Hospitals, Jubilee Hills"
    )

    now_iso = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    tier_1 = ESCALATION_TIERS[0]

    initial_matches = find_donor_matches(
        request_latitude=payload.latitude,
        request_longitude=payload.longitude,
        requested_blood_group=payload.blood_group,
        max_radius_km=tier_1[
            "radius_km"
        ],
    )

    for match in initial_matches:

        notify_donor(
            match["donor_id"],
            match["name"],
            request_id,
            payload.blood_group,
            hospital_name=hospital,
            urgency=payload.urgency,
            distance_km=match[
                "distance_km"
            ],
        )

    request_data = {

        "id": request_id,

        "blood_group":
            payload.blood_group,

        "units_required":
            payload.units_required,

        "urgency":
            payload.urgency,

        "latitude":
            payload.latitude,

        "longitude":
            payload.longitude,

        "hospital_name":
            hospital,

        "status":
            "searching",

        "confirmed_donors":
            [],

        "current_tier":
            tier_1["tier"],

        "tier_started_at":
            now_iso,

        "notified_donor_ids":
            [
                m["donor_id"]
                for m in initial_matches
            ],

        "created_at":
            now_iso,
    }

    saved = save_request(
        request_data
    )

    log_event(
        "EMERGENCY",
        f"Ticket {request_id} created | "
        f"{payload.blood_group} "
        f"({payload.units_required} units) | "
        f"{hospital} | "
        f"tier 1 notified "
        f"{len(initial_matches)} donor(s)",
    )

    return saved


# ============================================================
# LIST ALL REQUESTS
# ============================================================

@app.get("/requests")
def list_requests():

    if supabase:

        try:

            res = (
                supabase
                .table("blood_requests")
                .select("*")
                .order(
                    "created_at",
                    desc=True,
                )
                .execute()
            )

            return res.data or []

        except Exception as exc:

            log_event(
                "DATABASE",
                f"Query error: {exc}. "
                "Returning cached requests.",
            )

    return list(
        mock_requests.values()
    )


# ============================================================
# GET SINGLE REQUEST
# ============================================================

@app.get("/requests/{request_id}")
def get_request(
    request_id: str,
):

    return get_request_from_storage(
        request_id
    )


# ============================================================
# MATCHING ENGINE
# ============================================================

@app.get(
    "/requests/{request_id}/matches"
)
def get_ranked_matches(
    request_id: str,
    radius_km: float = Query(
        default=15.0,
        ge=1.0,
        le=100.0,
    ),
):

    req_data = get_request_from_storage(
        request_id
    )

    matches = find_donor_matches(
        request_latitude=
            req_data["latitude"],

        request_longitude=
            req_data["longitude"],

        requested_blood_group=
            req_data["blood_group"],

        max_radius_km=radius_km,
    )

    log_event(
        "MATCH_ENGINE",
        f"{request_id}: "
        f"{len(matches)} donors mapped "
        f"within {radius_km} km",
    )

    return {

        "request_id":
            request_id,

        "blood_group":
            req_data["blood_group"],

        "radius_km":
            radius_km,

        "match_count":
            len(matches),

        "matches":
            matches,
    }


# ============================================================
# DONOR RESPONSE
# ============================================================

@app.post(
    "/requests/{request_id}/respond"
)
def record_donor_response(
    request_id: str,
    response: DonorResponse,
):

    req_data = get_request_from_storage(
        request_id
    )

    if req_data.get("status") in {
        "closed",
        "cancelled",
        "escalated_to_blood_bank",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "This emergency request is "
                "no longer accepting donor responses."
            ),
        )

    confirmed = (
        req_data.get(
            "confirmed_donors"
        )
        or []
    )

    # --------------------------------------------------------
    # ACCEPT
    # --------------------------------------------------------

    if response.action == "accept":

        if any(
            d.get("donor_id")
            == response.donor_id
            for d in confirmed
        ):

            return {

                "request_id":
                    request_id,

                "status":
                    req_data.get(
                        "status"
                    ),

                "confirmed_count":
                    len(confirmed),

                "units_required":
                    req_data[
                        "units_required"
                    ],

                "message":
                    "Donor already confirmed.",
            }

        confirmed.append(
            {
                "donor_id":
                    response.donor_id,

                "confirmed_at":
                    datetime.now(
                        timezone.utc
                    ).isoformat(),
            }
        )

        new_status = (
            "fulfilled"
            if len(confirmed)
            >= req_data[
                "units_required"
            ]
            else "partially_fulfilled"
        )

        update_request(
            request_id,
            {
                "confirmed_donors":
                    confirmed,

                "status":
                    new_status,
            },
        )

        mark_notifications_responded(
            response.donor_id,
            request_id,
        )

        log_event(
            "DONOR_RESPONSE",
            f"Donor {response.donor_id} "
            f"accepted {request_id}. "
            f"Status: {new_status} "
            f"({len(confirmed)}/"
            f"{req_data['units_required']})",
        )

        return {

            "request_id":
                request_id,

            "status":
                new_status,

            "confirmed_count":
                len(confirmed),

            "units_required":
                req_data[
                    "units_required"
                ],

            "message":
                "Donation response recorded successfully.",
        }

    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

    mark_notifications_responded(
        response.donor_id,
        request_id,
    )

    log_event(
        "DONOR_RESPONSE",
        f"Donor {response.donor_id} "
        f"declined {request_id}",
    )

    return {

        "request_id":
            request_id,

        "action":
            "reject",

        "message":
            "Decline acknowledged.",
    }


# ============================================================
# DONOR AVAILABILITY
# ============================================================

@app.patch(
    "/donors/{donor_id}/availability"
)
def toggle_donor_availability(
    donor_id: str,
    update: AvailabilityUpdate,
):

    if supabase:

        try:

            res = (
                supabase
                .table("donors")
                .update(
                    {
                        "is_available":
                            update.is_available
                    }
                )
                .eq("id", donor_id)
                .execute()
            )

            if not res.data:

                raise HTTPException(
                    status_code=404,
                    detail="Donor profile not found.",
                )

        except HTTPException:
            raise

        except Exception as exc:

            log_event(
                "DATABASE",
                f"Availability update failed: {exc}",
            )

    else:

        donor_found = False

        for donor in mock_donors:

            if donor["id"] == donor_id:

                donor[
                    "is_available"
                ] = update.is_available

                donor_found = True
                break

        if not donor_found:

            raise HTTPException(
                status_code=404,
                detail="Donor profile not found.",
            )

    log_event(
        "DONOR_STATUS",
        f"Donor {donor_id} "
        f"availability set to "
        f"{update.is_available}",
    )

    return {

        "donor_id":
            donor_id,

        "is_available":
            update.is_available,
    }


# ============================================================
# DONOR NOTIFICATIONS
# ============================================================

@app.get(
    "/donors/{donor_id}/notifications"
)
def get_donor_notifications(
    donor_id: str,

    status: Optional[
        Literal[
            "pending",
            "responded",
        ]
    ] = Query(
        default="pending"
    ),
):

    notes = donor_notifications.get(
        donor_id,
        [],
    )

    if status:

        notes = [
            n
            for n in notes
            if n["status"] == status
        ]

    notes = sorted(
        notes,
        key=lambda n: n["created_at"],
        reverse=True,
    )

    return {

        "donor_id":
            donor_id,

        "count":
            len(notes),

        "notifications":
            notes,
    }


# ============================================================
# BLOOD BANK FALLBACK
# ============================================================

@app.get(
    "/requests/{request_id}/blood-banks"
)
def get_blood_bank_fallback(
    request_id: str,

    radius_km: float = Query(
        default=25.0,
        ge=1.0,
        le=100.0,
    ),
):

    req_data = get_request_from_storage(
        request_id
    )

    banks = find_nearby_blood_banks(
        req_data["latitude"],
        req_data["longitude"],
        radius_km,
    )

    return {

        "request_id":
            request_id,

        "radius_km":
            radius_km,

        "bank_count":
            len(banks),

        "blood_banks":
            banks,
    }
