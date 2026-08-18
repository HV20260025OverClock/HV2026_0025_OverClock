/**
 * RedAid — mock API layer.
 *
 * Every function here is shaped like the real FastAPI + Supabase endpoints will
 * be, so wiring the real backend later is a drop-in swap. All functions are
 * async and return Promises with a small simulated latency.
 */

export const BLOOD_GROUPS = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']

const delay = (ms) => new Promise((res) => setTimeout(res, ms))

/* ------------------------------------------------------------------ */
/* Blood stock inventory                                              */
/* ------------------------------------------------------------------ */

// units on hand vs a per-group safe threshold
let STOCK = [
  { group: 'O+', units: 42, threshold: 30, plasma: 18, platelets: 12 },
  { group: 'O-', units: 9, threshold: 20, plasma: 6, platelets: 4 },
  { group: 'A+', units: 31, threshold: 25, plasma: 14, platelets: 9 },
  { group: 'A-', units: 7, threshold: 12, plasma: 3, platelets: 2 },
  { group: 'B+', units: 26, threshold: 20, plasma: 11, platelets: 7 },
  { group: 'B-', units: 5, threshold: 10, plasma: 2, platelets: 1 },
  { group: 'AB+', units: 15, threshold: 10, plasma: 5, platelets: 4 },
  { group: 'AB-', units: 3, threshold: 8, plasma: 1, platelets: 1 },
]

export async function getStock() {
  await delay(650)
  return STOCK.map((s) => ({ ...s }))
}

export async function updateStockCell(group, field, value) {
  await delay(300)
  STOCK = STOCK.map((s) =>
    s.group === group ? { ...s, [field]: Math.max(0, Math.round(value)) } : s,
  )
  return STOCK.find((s) => s.group === group)
}

/* ------------------------------------------------------------------ */
/* Request trend history                                              */
/* ------------------------------------------------------------------ */

function buildTrend(days) {
  const out = []
  const now = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(now.getDate() - i)
    const base = 4 + Math.sin(i / 3) * 3
    out.push({
      date: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      requests: Math.max(1, Math.round(base + Math.random() * 4)),
      fulfilled: Math.max(0, Math.round(base - 1 + Math.random() * 3)),
    })
  }
  return out
}

export async function getTrend(range = 7) {
  await delay(700)
  return buildTrend(range)
}

/* ------------------------------------------------------------------ */
/* Active requests                                                    */
/* ------------------------------------------------------------------ */

export const REQUEST_STATUS = {
  SEARCHING: 'Searching',
  MATCHES: 'Matches Found',
  CONFIRMED: 'Donor Confirmed',
  FULFILLED: 'Fulfilled',
}

let REQUESTS = [
  {
    id: 'REQ-2481',
    patient: 'Trauma — Bay 3',
    group: 'O-',
    units: 4,
    urgency: 'Critical',
    status: 'Searching',
    createdAt: Date.now() - 1000 * 60 * 4,
    ward: 'Emergency',
  },
  {
    id: 'REQ-2479',
    patient: 'Post-partum hemorrhage',
    group: 'A+',
    units: 2,
    urgency: 'Urgent',
    status: 'Matches Found',
    createdAt: Date.now() - 1000 * 60 * 22,
    ward: 'Obstetrics',
  },
  {
    id: 'REQ-2475',
    patient: 'Scheduled surgery — Kumar',
    group: 'B+',
    units: 3,
    urgency: 'Routine',
    status: 'Donor Confirmed',
    createdAt: Date.now() - 1000 * 60 * 55,
    ward: 'Surgery',
  },
  {
    id: 'REQ-2470',
    patient: 'Anemia transfusion',
    group: 'AB+',
    units: 1,
    urgency: 'Routine',
    status: 'Fulfilled',
    createdAt: Date.now() - 1000 * 60 * 140,
    ward: 'Internal Med',
  },
]

export async function getRequests() {
  await delay(600)
  return REQUESTS.map((r) => ({ ...r }))
}

export async function getRequest(id) {
  await delay(400)
  const r = REQUESTS.find((x) => x.id === id)
  return r ? { ...r } : null
}

export async function createRequest(payload) {
  await delay(1100)
  const id = `REQ-${2482 + Math.floor(Math.random() * 400)}`
  const req = {
    id,
    patient: payload.patient || 'Unnamed case',
    group: payload.group,
    units: payload.units,
    urgency: payload.urgency,
    notes: payload.notes || '',
    ward: payload.ward || 'Emergency',
    status: 'Searching',
    createdAt: Date.now(),
  }
  REQUESTS = [req, ...REQUESTS]
  return req
}

/* ------------------------------------------------------------------ */
/* Live donor matching                                                */
/* ------------------------------------------------------------------ */

const DONOR_POOL = [
  { name: 'Aarav Sharma', distanceKm: 1.2, etaMin: 6, lastDonation: '3 months ago' },
  { name: 'Priya Nair', distanceKm: 2.4, etaMin: 9, lastDonation: '5 months ago' },
  { name: 'Rohan Mehta', distanceKm: 3.1, etaMin: 12, lastDonation: '4 months ago' },
  { name: 'Sara Iyer', distanceKm: 4.6, etaMin: 15, lastDonation: '7 months ago' },
  { name: 'Vikram Rao', distanceKm: 5.8, etaMin: 19, lastDonation: '2 months ago' },
  { name: 'Neha Gupta', distanceKm: 6.9, etaMin: 22, lastDonation: '6 months ago' },
  { name: 'Karthik Menon', distanceKm: 8.3, etaMin: 27, lastDonation: '8 months ago' },
]

/**
 * Simulate the matching engine streaming donors in over time.
 * `onDonor` is called for each donor as it is "found".
 * Returns a cleanup function to cancel pending timers.
 */
export function streamDonorMatches(request, onDonor) {
  const timers = []
  const pool = DONOR_POOL.slice(0, 5 + Math.floor(Math.random() * 2))
  pool.forEach((d, i) => {
    const t = setTimeout(
      () => {
        onDonor({
          id: `DNR-${1000 + i}`,
          ...d,
          group: request?.group ?? 'O-',
          status: 'Notified',
        })
      },
      900 + i * (700 + Math.random() * 500),
    )
    timers.push(t)
  })
  return () => timers.forEach(clearTimeout)
}

/**
 * Simulate a donor progressing Notified -> Viewing -> Accepted/Declined.
 * `onStatus` receives the new status string.
 */
export function simulateDonorProgress(donor, onStatus, { accept = false } = {}) {
  const timers = []
  timers.push(
    setTimeout(() => onStatus('Viewing'), 1200 + Math.random() * 1500),
  )
  timers.push(
    setTimeout(
      () => onStatus(accept ? 'Accepted' : 'Declined'),
      3200 + Math.random() * 2200,
    ),
  )
  return () => timers.forEach(clearTimeout)
}

/* ------------------------------------------------------------------ */
/* Request timeline                                                   */
/* ------------------------------------------------------------------ */

export async function getRequestTimeline(id) {
  await delay(500)
  const now = Date.now()
  return [
    { key: 'raised', label: 'Request Raised', at: now - 1000 * 60 * 55, done: true },
    { key: 'matching', label: 'Matching Donors', at: now - 1000 * 60 * 52, done: true },
    { key: 'found', label: 'Donor Found', at: now - 1000 * 60 * 44, done: true },
    { key: 'enroute', label: 'Donor En Route', at: now - 1000 * 60 * 12, done: true },
    { key: 'fulfilled', label: 'Fulfilled', at: null, done: false },
  ]
}
