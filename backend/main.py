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
@app.get("/donors/{donor_id}/notifications")
def get_donor_notifications(
    donor_id: str,
    status: str = "pending"
):
    if not supabase:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not connected."
        )

    try:
        # First find the donor's user_id
        donor_response = (
            supabase
            .table("donors")
            .select("id,user_id")
            .eq("id", donor_id)
            .limit(1)
            .execute()
        )

        if not donor_response.data:
            raise HTTPException(
                status_code=404,
                detail="Donor not found"
            )

        user_id = donor_response.data[0]["user_id"]

        # Notifications belong to the user, not directly to the donor
        query = (
            supabase
            .table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )

        # Your schema has is_read, not a status column.
        if status == "pending":
            query = query.eq("is_read", False)

        response = query.execute()

        notifications = response.data or []

        return {
            "count": len(notifications),
            "notifications": notifications
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"[NOTIFICATIONS] Lookup failed: {exc}",
            flush=True
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch notifications: {exc}"
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