import { useState } from "react";
import "./App.css";
import {
  createEmergencyRequest,
  getMatches,
} from "./services/api";

function App() {
  const [bloodGroup, setBloodGroup] = useState("A+");
  const [units, setUnits] = useState(1);
  const [urgency, setUrgency] = useState("critical");
  const [hospitalName, setHospitalName] = useState(
    "RedAid Demo Hospital"
  );

  // Request state
  const [requestCreated, setRequestCreated] = useState(false);
  const [requestId, setRequestId] = useState("");
  const [matches, setMatches] = useState([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setRequestCreated(false);
    setMatches([]);

    try {
      // 1. Create emergency request in FastAPI
      const request = await createEmergencyRequest({
        blood_group: bloodGroup,
        units_required: units,
        urgency: urgency,
        latitude: 17.3850,
        longitude: 78.4867,
        hospital_name: hospitalName,
      });

      console.log("Emergency request created:", request);

      // 2. Store the real request ID returned by FastAPI
      setRequestId(request.id);
      setRequestCreated(true);

      // 3. Ask FastAPI for donor matches
      const matchData = await getMatches(request.id);

      console.log("Donor matches:", matchData);

      // 4. Store real donor matches
      setMatches(matchData.matches || []);
    } catch (err) {
      console.error("Failed to create emergency request:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to create emergency request"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">

      {/* HEADER */}
      <header className="header">
        <div>
          <div className="brand">REDAID</div>

          <h1>Hospital Dashboard</h1>

          <p>
            Emergency blood request and donor discovery
          </p>
        </div>

        <div className="hospital-badge">
          🏥 {hospitalName}
        </div>
      </header>


      {/* STATISTICS */}
      <section className="stats">

        <div className="stat-card">
          <span>Active Requests</span>
          <strong>{requestCreated ? 1 : 0}</strong>
        </div>

        <div className="stat-card critical">
          <span>Critical</span>
          <strong>
            {requestCreated && urgency === "critical" ? 1 : 0}
          </strong>
        </div>

        <div className="stat-card">
          <span>Units Required</span>
          <strong>
            {requestCreated ? units : 0}
          </strong>
        </div>

        <div className="stat-card success">
          <span>Fulfilled</span>
          <strong>0</strong>
        </div>

      </section>


      <div className="dashboard-grid">

        {/* CREATE REQUEST */}
        <section className="card">

          <div className="card-header">

            <div>
              <h2>Emergency Blood Request</h2>

              <p>
                Create a request to find compatible donors.
              </p>
            </div>

            <span className="emergency-label">
              EMERGENCY
            </span>

          </div>


          <form onSubmit={handleSubmit}>

            {/* Blood Group */}
            <label>
              Blood Group

              <select
                value={bloodGroup}
                onChange={(event) =>
                  setBloodGroup(event.target.value)
                }
              >
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </select>
            </label>


            {/* Units */}
            <label>
              Units Required

              <input
                type="number"
                min="1"
                max="20"
                value={units}
                onChange={(event) =>
                  setUnits(Number(event.target.value))
                }
              />
            </label>


            {/* Urgency */}
            <label>
              Urgency

              <select
                value={urgency}
                onChange={(event) =>
                  setUrgency(event.target.value)
                }
              >
                <option value="normal">Normal</option>
<option value="urgent">Urgent</option>
<option value="critical">Critical</option>
              </select>
            </label>


            {/* Hospital */}
            <label>
              Hospital Name

              <input
                type="text"
                value={hospitalName}
                onChange={(event) =>
                  setHospitalName(event.target.value)
                }
              />
            </label>


            {/* Submit */}
            <button
              type="submit"
              className="primary-button"
              disabled={loading}
            >
              {loading
                ? "Creating Request..."
                : "Create Emergency Request"}
            </button>

          </form>


          {/* SUCCESS */}
          {requestCreated && (
            <div className="success-message">
              ✓ Emergency request created successfully.
              <br />

              <strong>
                Request ID: {requestId}
              </strong>
            </div>
          )}


          {/* ERROR */}
          {error && (
            <div className="error-message">
              ✕ {error}
            </div>
          )}

        </section>


        {/* ACTIVE REQUEST */}
        <section className="card">

          <div className="card-header">

            <div>
              <h2>Active Request</h2>

              <p>
                Current emergency status
              </p>
            </div>

            <span className="status searching">
              {requestCreated
                ? "SEARCHING"
                : "NO REQUEST"}
            </span>

          </div>


          {/* Request ID */}
          <div className="request-id">
            {requestId || "No active request"}
          </div>


          {/* Request details */}
          <div className="request-details">

            <div>
              <span>Blood Group</span>
              <strong>
                {requestCreated ? bloodGroup : "-"}
              </strong>
            </div>

            <div>
              <span>Units</span>
              <strong>
                {requestCreated ? units : "-"}
              </strong>
            </div>

            <div>
              <span>Urgency</span>
              <strong>
                {requestCreated
                  ? urgency
                  : "-"}
              </strong>
            </div>

            <div>
              <span>Search Radius</span>
              <strong>
                15 km
              </strong>
            </div>

          </div>


          {/* ESCALATION */}
          <div className="escalation">

            <h3>Donor Search</h3>


            <div className="tier active">

              <span className="dot"></span>

              <div>
                <strong>
                  Tier 1
                </strong>

                <small>
                  Within 5 km
                </small>
              </div>

              <span className="tier-status">
                Active
              </span>

            </div>


            <div className="tier">

              <span className="dot"></span>

              <div>
                <strong>
                  Tier 2
                </strong>

                <small>
                  Within 10 km
                </small>
              </div>

              <span className="tier-status">
                Waiting
              </span>

            </div>


            <div className="tier">

              <span className="dot"></span>

              <div>
                <strong>
                  Tier 3
                </strong>

                <small>
                  Within 20 km
                </small>
              </div>

              <span className="tier-status">
                Waiting
              </span>

            </div>

          </div>

        </section>

      </div>


      {/* DONOR MATCHES */}
      <section className="card matches-card">

        <div className="card-header">

          <div>
            <h2>
              Potential Donors
            </h2>

            <p>
              Ranked by compatibility,
              distance and priority.
            </p>
          </div>


          <span className="match-count">
            {matches.length}{" "}
            {matches.length === 1
              ? "match"
              : "matches"}
          </span>

        </div>


        <div className="donor-grid">

          {matches.length === 0 ? (

            <p>
              {requestCreated
                ? "No donor matches found."
                : "Create an emergency request to find donors."}
            </p>

          ) : (

            matches.map((donor) => (

              <DonorCard
                key={donor.donor_id}
                name={donor.name}
                blood={donor.blood_group}
                distance={`${donor.distance_km} km`}
                score={donor.priority_score}
                exact={donor.is_exact_match}
                status={donor.status}
              />

            ))

          )}

        </div>

      </section>

    </div>
  );
}


/* ============================================================
   DONOR CARD
============================================================ */

function DonorCard({
  name,
  blood,
  distance,
  score,
  exact,
  status,
}) {
  return (
    <div className="donor-card">

      <div className="donor-top">

        <div>

          <h3>
            {name}
          </h3>

          <p>
            Available donor
          </p>

        </div>


        <div className="blood-badge">
          {blood}
        </div>

      </div>


      <div className="donor-info">

        <div>
          <span>
            Distance
          </span>

          <strong>
            {distance}
          </strong>
        </div>


        <div>
          <span>
            Priority
          </span>

          <strong>
            {score}
          </strong>
        </div>


        <div>
          <span>
            Match
          </span>

          <strong>
            {exact
              ? "Exact"
              : "Compatible"}
          </strong>
        </div>

      </div>


      <div className="donor-status">
        ● {status || "NOTIFIED"}
      </div>

    </div>
  );
}


export default App;