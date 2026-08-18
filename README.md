# RedAid — Smart Blood Donor Discovery & Emergency Blood Register Platform

RedAid is a smart blood donor discovery and emergency blood request platform that connects hospitals with nearby, eligible blood donors.

When a hospital creates an emergency blood request, RedAid identifies compatible and available donors, ranks them based on relevant factors such as distance and donation history, and notifies the most suitable donors. If the initial search area does not provide enough responses, the system can progressively expand the search radius.

The goal of RedAid is to make emergency blood discovery faster, more structured, and easier to track than traditional methods such as phone calls, WhatsApp broadcasts, and word of mouth.

---

## Problem Statement

During emergency situations, hospitals often depend on manual communication methods to find suitable blood donors. This process can be slow, difficult to coordinate, and challenging to track.

Common challenges include:

* Difficulty finding compatible donors quickly
* Manual calling and messaging of multiple donors
* No centralized view of donor availability
* Difficulty prioritizing nearby and suitable donors
* Limited visibility into donor responses
* Delays when the initial pool of donors is insufficient
* Lack of a structured audit trail for emergency requests

RedAid addresses these challenges through a centralized platform that connects hospitals and donors through an intelligent matching and notification workflow.

---

## Solution

RedAid provides a structured emergency blood discovery workflow:

1. A hospital creates an emergency blood request.
2. The system identifies compatible, available, verified, and eligible donors.
3. Donors are filtered based on their location and the current search radius.
4. Matching donors are ranked using factors such as distance, donation recency, and reliability.
5. Selected donors receive an emergency notification.
6. Donors can accept or decline the request.
7. The hospital dashboard reflects donor responses and request status.
8. If insufficient donors respond within the defined wait window, the system expands the search radius and identifies additional donors.
9. All important request status changes are recorded for tracking and auditing.

---

## System Overview

```text
                   +----------------------+
                   |   Hospital Dashboard  |
                   |    React + Vite       |
                   +----------+-----------+
                              |
                              v
                    +-------------------+
                    |    FastAPI API    |
                    |   Python Backend   |
                    +---------+---------+
                              |
                              v
              +-------------------------------+
              | Supabase PostgreSQL + PostGIS |
              |      Matching Engine          |
              +---------------+---------------+
                              ^
                              |
                    +---------+---------+
                    |    Donor Mobile   |
                    |   Flutter / Dart  |
                    +-------------------+
```

---

## Core Features

### Donor Management

* Donor registration and profile management
* Blood group information
* Donor location
* Availability status
* Donation history
* Eligibility information
* Verified donor status

### Emergency Blood Requests

Hospitals can create emergency requests containing information such as:

* Required blood group
* Number of units required
* Hospital location
* Urgency level
* Request status
* Required response time

### Smart Donor Matching

The matching engine identifies suitable donors by considering:

* Blood-type compatibility
* Donor availability
* Donor eligibility
* Donor verification status
* Geographic distance
* Donation recency
* Donor reliability

The result is a ranked list of potential donors rather than an unfiltered list of registered users.

### Dynamic Search Radius

RedAid can progressively expand the donor search area when the initial donor pool does not provide enough responses.

Example:

```text
0–5 km
   |
   | Insufficient responses
   v
5–10 km
   |
   | Still insufficient
   v
10–20 km
```

The system avoids sending duplicate notifications to donors who have already been contacted for the same request.

### Donor Response System

Donors can respond directly to an emergency request by:

* Accepting the request
* Declining the request

The hospital can then monitor the responses and determine the current coverage of the request.

### Request Tracking

Hospitals can monitor:

* Pending donor responses
* Accepted donors
* Declined responses
* Request status
* Number of required units
* Current donor coverage

### Audit Trail

Important request and response events are recorded to provide a history of status changes and actions associated with an emergency request.

---

## Why RedAid?

| Traditional Approach        | RedAid                             |
| --------------------------- | ---------------------------------- |
| Manual phone calls          | Structured digital requests        |
| WhatsApp broadcasts         | Targeted donor notifications       |
| Manual donor selection      | Ranked donor matching              |
| Fixed search area           | Dynamic search radius              |
| Difficult response tracking | Centralized response tracking      |
| Scattered information       | Centralized donor and request data |
| Limited request history     | Request status audit trail         |

RedAid is designed to reduce the time and effort required to identify suitable donors during emergency situations while providing hospitals with better visibility into the request lifecycle.

---

## Architecture

### Data Model

Core database entities include:

```text
users
donors
hospitals
blood_requests
donor_responses
notifications
request_status_history
blood_compatibility
```

The `blood_compatibility` table provides the lookup rules used by the matching system to determine compatible donor and recipient blood groups.

### Matching Pipeline

```text
Emergency Blood Request
          |
          v
Blood-Type Compatibility
          |
          v
Availability Filter
          |
          v
Verification & Eligibility
          |
          v
PostGIS Distance Filtering
          |
          v
Priority Scoring
          |
          v
Ranked Donor List
          |
          v
Donor Notifications
```

Example matching result:

```json
{
  "donor_id": "d1f2...",
  "distance_km": 2.4,
  "score": 92.0
}
```

### Priority Scoring

The matching engine can consider multiple factors when ranking donors:

```text
Priority Score
    |
    +-- Distance
    |
    +-- Donation Recency
    |
    +-- Donor Reliability
    |
    +-- Request Urgency
```

The exact scoring weights can be adjusted according to the application's requirements.

---

## Dynamic Escalation

The escalation mechanism allows the system to expand the search radius when the current donor pool does not provide enough responses.

```text
Initial Request
      |
      v
Search within 5 km
      |
      v
Enough responses?
   /          \
 Yes           No
 |              |
 v              v
Continue      Expand to 10 km
                 |
                 v
            Enough responses?
             /          \
           Yes           No
            |             |
            v             v
         Continue      Expand to 20 km
```

The escalation process can be executed through scheduled backend jobs or database functions.

---

## Technology Stack

| Layer                    | Technology                         |
| ------------------------ | ---------------------------------- |
| Donor Mobile Application | Flutter, Dart                      |
| Backend API              | Python, FastAPI                    |
| Database                 | Supabase PostgreSQL                |
| Geospatial Queries       | PostGIS                            |
| Matching Engine          | PostgreSQL / SQL Functions, Python |
| Hospital Dashboard       | React, Vite                        |
| Dashboard Styling        | Tailwind CSS                       |
| API Documentation        | FastAPI Swagger UI                 |

---

## API Reference

All API endpoints are served by the FastAPI backend.

| Method | Endpoint                    | Description                       |
| ------ | --------------------------- | --------------------------------- |
| GET    | `/`                         | Backend health check              |
| GET    | `/donors/{id}`              | Get donor profile                 |
| PATCH  | `/donors/{id}/availability` | Update donor availability         |
| POST   | `/requests`                 | Create an emergency blood request |
| GET    | `/requests`                 | List blood requests               |
| GET    | `/requests/{id}`            | Get a specific blood request      |
| PATCH  | `/requests/{id}/status`     | Update request status             |
| GET    | `/requests/{id}/matches`    | Get ranked donor matches          |
| POST   | `/requests/{id}/respond`    | Accept or decline a donor match   |

### Interactive API Documentation

When the backend is running, FastAPI provides interactive API documentation at:

```text
http://localhost:8000/docs
```

---

## Project Structure

```text
RedAid/
|
+-- backend/
|   +-- app/
|   |   +-- main.py
|   |   +-- routes/
|   |   +-- services/
|   |   +-- models/
|   |   +-- ...
|   +-- requirements.txt
|   +-- .env.example
|
+-- dashboard/
|   +-- src/
|   +-- package.json
|   +-- ...
|
+-- mobile/
|   +-- lib/
|   +-- pubspec.yaml
|   +-- ...
|
+-- database/
|   +-- schema.sql
|   +-- seed.sql
|   +-- functions.sql
|
+-- docs/
|   +-- images/
|   +-- ...
|
+-- README.md
```

---

## Getting Started

### Prerequisites

Make sure the following are installed:

* Python 3.11 or later
* Node.js 18 or later
* Flutter SDK
* Git
* A Supabase project
* PostgreSQL with PostGIS enabled through Supabase

---

## 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd RedAid
```

---

## 2. Configure the Database

Create a Supabase project and enable the required PostgreSQL and PostGIS functionality.

Run the database scripts in the following order:

```text
database/schema.sql
database/seed.sql
database/functions.sql
```

These scripts create the required tables, seed/demo data, compatibility rules, and database functions used by the application.

---

## 3. Configure the Backend

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Create the environment configuration file:

```bash
cp .env.example .env
```

On Windows, if `cp` is unavailable, create `.env` manually from `.env.example`.

Configure the required Supabase credentials in `.env`:

```text
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
```

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The backend will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## 4. Run the Hospital Dashboard

Open a new terminal and navigate to the dashboard:

```bash
cd dashboard
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the URL displayed by Vite in your browser.

---

## 5. Run the Donor Mobile Application

Open another terminal and navigate to the mobile application:

```bash
cd mobile
```

Install Flutter dependencies:

```bash
flutter pub get
```

Run the application:

```bash
flutter run
```

Make sure an emulator, simulator, or physical device is connected.

---

## Environment Variables

The backend requires Supabase configuration.

Example:

```text
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
```

Do not commit `.env` files or private API keys to the repository.

Use `.env.example` to document required environment variables without exposing secrets.

---

## Demo Workflow

The intended demonstration flow is:

```text
Hospital Login
      |
      v
Create Emergency Blood Request
      |
      v
Matching Engine
      |
      v
Find Compatible Donors
      |
      v
Rank Donors by Priority
      |
      v
Notify Donors
      |
      v
Donor Accepts / Declines
      |
      v
Hospital Dashboard Updates
      |
      v
Request Fulfilled / Escalated
```

This workflow demonstrates the core purpose of RedAid: connecting emergency blood requests with suitable donors through an automated matching process.

---

## Security and Privacy Considerations

Because RedAid handles donor and hospital information, security and privacy are important parts of the platform.

The system is designed with the following considerations:

* Role-based access for donors, hospitals, and administrators
* Authentication for protected operations
* Restricted access to donor information
* Secure handling of location information
* Protection of Supabase credentials and API keys
* Request and response audit history
* Validation of emergency request data

Production deployment should additionally include appropriate authentication, authorization, encryption, rate limiting, logging, and privacy controls.

---

## Current Status

The project is being developed as a hackathon prototype.

### Core Development

* [ ] Complete donor registration flow
* [ ] Complete hospital registration flow
* [ ] Complete authentication and role-based access
* [ ] Complete emergency request creation
* [ ] Complete donor matching
* [ ] Complete donor accept/decline workflow
* [ ] Complete hospital request tracking
* [ ] Complete dynamic radius escalation
* [ ] Complete notification system
* [ ] Complete audit trail
* [ ] End-to-end integration testing

---

## Roadmap

Future improvements may include:

* Push notifications for emergency donor alerts
* SMS fallback for donors without the mobile application
* Donation history and analytics
* Hospital analytics dashboard
* Advanced donor reliability scoring
* Improved matching algorithms
* Admin verification workflows
* Real-time request updates
* Production-grade authentication and authorization
* Deployment to cloud infrastructure
* Monitoring and observability

---

## Team

| Member   | Responsibility               | Technology                            |
| -------- | ---------------------------- | ------------------------------------- |
| Member 1 | Donor Mobile Application     | Flutter, Dart                         |
| Member 2 | Backend API and Integration  | Python, FastAPI                       |
| Member 3 | Database and Matching Engine | Supabase, PostgreSQL, PostGIS, Python |
| Member 4 | Hospital Dashboard and Demo  | React, Vite, Tailwind CSS             |

---

## Future Vision

RedAid aims to provide a reliable digital infrastructure for emergency blood discovery by reducing dependence on manual donor searches.

The long-term vision is to create a scalable platform where hospitals can quickly identify suitable donors while donors receive relevant emergency requests based on compatibility, availability, and location.

---

## License

This project is currently developed as a hackathon prototype.

A suitable open-source license, such as the MIT License, can be added before making the repository public.

---

## Disclaimer

RedAid is a technology prototype intended to support blood donor discovery and emergency request coordination.

It does not replace medical professionals, hospital blood banks, laboratory testing, blood-group verification, eligibility assessment, or applicable healthcare regulations.

All donor eligibility and blood transfusion decisions must be verified by qualified medical professionals and authorized blood-bank personnel.

