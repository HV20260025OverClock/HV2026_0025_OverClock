const API_URL = "https://hv2026-0025-overclock.onrender.com";

export async function createEmergencyRequest(data) {
  const response = await fetch(`${API_URL}/requests`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      typeof result.detail === "string"
        ? result.detail
        : "Failed to create emergency request"
    );
  }

  return result;
}

export async function getMatches(requestId) {
  const response = await fetch(
    `${API_URL}/requests/${requestId}/matches?radius_km=15`
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      typeof result.detail === "string"
        ? result.detail
        : "Failed to load donor matches"
    );
  }

  return result;
}