const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function createEmergencyRequest(data: {
  blood_group: string;
  units_required: number;
  urgency: string;
  latitude: number;
  longitude: number;
  hospital_name: string;
}) {
  const response = await fetch(`${API_BASE_URL}/requests`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Failed to create emergency request");
  }

  return response.json();
}

export async function getDonorMatches(requestId: string) {
  const response = await fetch(
    `${API_BASE_URL}/requests/${requestId}/matches?radius_km=5`
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Failed to fetch donor matches");
  }

  return response.json();
}

export async function respondToRequest(
  requestId: string,
  donorId: string,
  action: "accept" | "reject"
) {
  const response = await fetch(
    `${API_BASE_URL}/requests/${requestId}/respond`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        donor_id: donorId,
        action,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Failed to respond to request");
  }

  return response.json();
}
