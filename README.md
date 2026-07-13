
### AI-Powered Medical Records & Pharmacy Management Platform

> **MedFlow AI** is a modern healthcare management platform that combines secure medical record management, pharmacy operations, graph-based relationship analytics, and AI-powered clinical assistance into a single application.

---

# Table of Contents

- Overview
- Features
- Tech Stack
- System Architecture
- Project Structure
- Core Modules
- AI Integration (Sarvam AI)
- Graph Analytics (Neo4j)
- Mobile Application (Expo)
- Installation
- Environment Variables
- Running the Project
- API Features
- Future Enhancements
- License
- Author

---

# Overview

MedFlow AI is a **Full-Stack Healthcare Management System** developed using **FastAPI**, **React (Vite)**, **PostgreSQL**, **Neo4j**, and **Sarvam AI**.

The platform provides secure healthcare management through **Role-Based Access Control (RBAC)**, enabling different user experiences for administrators, pharmacists, and patients.

Unlike traditional healthcare systems that only store relational data, MedFlow AI also utilizes **Neo4j Graph Database** to model complex relationships among patients, prescriptions, medications, doctors, and pharmacies. This enables intelligent graph queries and healthcare analytics.

Additionally, the platform integrates **Sarvam AI** to provide AI-powered clinical assistance, including medication guidance, dosage suggestions, and drug interaction warnings.

An optional **Expo (React Native)** mobile application allows healthcare professionals and patients to access the same backend services on Android and iOS.

---

#  Key Features

## Authentication & Security

- JWT Authentication
- Role-Based Access Control (RBAC)
- Protected API Endpoints
- Secure Password Hashing
- Session Management

---

##  User Roles

### Admin

- Dashboard
- User Management
- Analytics
- Reports
- System Monitoring
- Manage Patients
- Manage Pharmacists

---

###  Pharmacist

- Prescription Verification
- Inventory Management
- Medicine Tracking
- Prescription History
- Medicine Availability

---

###  Patient

- View Medical Records
- View Prescriptions
- Personal Dashboard
- Health Summary
- Profile Management

---

# Highlighted Technologies

---

# Neo4j Graph Database

Unlike traditional SQL databases, **Neo4j** stores relationships as first-class entities.

### Why Neo4j?

Healthcare data contains complex relationships such as:

```
Patient
   │
Visited
   │
Doctor
   │
Prescribed
   │
Medicine
   │
Available At
   │
Pharmacy
```

Neo4j allows the application to analyze these relationships efficiently.

### Example Use Cases

- Drug Interaction Networks
- Patient Prescription History
- Frequently Prescribed Medicines
- Doctor-Patient Relationship Analysis
- Pharmacy Supply Network
- Disease Similarity Analysis
- Recommendation Systems

### Benefits

- High-performance graph traversal
- Relationship analytics
- Better visualization
- Real-time healthcare insights
- Network-based recommendations

---

#  Sarvam AI Integration

MedFlow AI integrates **Sarvam AI** as an intelligent clinical assistant.

The AI module helps healthcare professionals make better decisions by analyzing medical prompts.

### AI Features

- Medicine Suggestions
- Dosage Recommendations
- Drug Interaction Warnings
- Prescription Summarization
- Clinical Notes Generation
- Medical Question Answering
- Healthcare Assistant Chat

### Example API

```
POST /ai/suggest
```

Example Request

```json
{
    "prompt": "Patient is prescribed Paracetamol and Ibuprofen."
}
```

Example Response

```json
{
    "suggestion": "Monitor dosage intervals. Avoid exceeding recommended daily limits."
}
```

### Benefits

- Faster clinical decisions
- Reduced medication errors
- AI-powered healthcare assistance
- Improved pharmacist productivity

---

# Expo Mobile Application

The project includes an optional **Expo React Native** application.

The mobile app consumes the same FastAPI backend used by the web application.

### Mobile Features

- Secure Login
- JWT Authentication
- Patient Dashboard
- Prescription Viewing
- Medicine Information
- Notifications
- Profile Management

### Advantages

- Cross-platform
- Android Support
- iOS Support
- Shared Backend
- Faster Development
- Easy Deployment

---

#  Tech Stack

| Layer | Technology |
|----------|----------------|
| Backend | FastAPI |
| Frontend | React (Vite) |
| Database | PostgreSQL |
| Graph Database | Neo4j |
| ORM | SQLAlchemy |
| Authentication | JWT |
| Password Security | Passlib |
| AI Assistant | Sarvam AI |
| Mobile | Expo (React Native) |
| Routing | React Router |
| Icons | React Icons |
| API Testing | Swagger UI |
| Environment | python-dotenv |
| Server | Uvicorn |
| Package Manager | uv |
| Deployment | Docker (Optional) |

---

#  Project Structure

```
MedFlow-AI/
│
├── backend/
│   ├── database/
│   ├── models/
│   ├── routes/
│   ├── services/
│   │      └── ai_service.py
│   ├── utils/
│   ├── tests/
│   ├── neo4j_driver.py
│   └── main.py
│
├── frontend/
│   ├── src/
│   ├── pages/
│   ├── components/
│   └── assets/
│
├── mobile/
│   └── Expo App
│
├── .env
├── README.md
└── requirements.txt
```

---

#  Core Modules

## Authentication

- Login
- Logout
- JWT
- Protected Routes

---

## User Management

- Admin CRUD
- Pharmacist CRUD
- Patient CRUD

---

## Medical Records

- Patient Records
- Prescriptions
- Medical History
- Health Summary

---

## Pharmacy Module

- Inventory
- Stock Management
- Medicine Tracking
- Prescription Handling

---

## Analytics

- User Statistics
- Inventory Reports
- Medicine Usage
- Graph Analytics (Neo4j)

---

#  System Architecture

```
                    React Web
                         │
                         │
                 React Native (Expo)
                         │
                         ▼
                 FastAPI Backend
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
 PostgreSQL        Neo4j        Sarvam AI
(Relational DB) (Graph DB)   (LLM Assistant)
```

---

# Environment Variables

Create a `.env` file inside the backend.

```env
DATABASE_URL=

JWT_SECRET_KEY=

NEO4J_URI=

NEO4J_USER=

NEO4J_PASSWORD=

SARVAM_API_KEY=
```

---

#  Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/MedFlow-AI.git

cd MedFlow-AI
```

---

## Backend

```bash
cd backend

uv pip install -r requirements.txt

uvicorn main:app --reload
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## Mobile

```bash
cd mobile

npm install

expo start
```

---

## Neo4j

1. Install Neo4j Desktop or use Neo4j Aura.

2. Configure

```
NEO4J_URI

NEO4J_USER

NEO4J_PASSWORD
```

3. Seed sample graph

```bash
python scripts/seed_graph.py
```

---

## Sarvam AI

Install

```bash
pip install sarvamai
```

Add API Key

```
SARVAM_API_KEY=YOUR_KEY
```

Start backend

```bash
uvicorn main:app --reload
```

Call

```
POST /ai/suggest
```

---

#  Future Enhancements

- Voice Assistant
- OCR Prescription Scanner
- Appointment Booking
- Doctor Portal
- AI Disease Prediction
- Medicine Recommendation Engine
- Drug Interaction Knowledge Graph
- Notification System
- Wearable Device Integration
- Medical Report Summarization
- Real-time Analytics Dashboard

---

#  License

This project is licensed under the **MIT License**.

---

#  Author

**Pranav Shankar**

AI & Full Stack Developer

GitHub: https://github.com/pranavshankar1221

---

#  Support

If you found this project helpful, consider giving it a **⭐ Star** on GitHub.

Contributions, issues, and feature requests are always welcome!

---

##  Why MedFlow AI?

MedFlow AI goes beyond a conventional healthcare management system by combining:

-  Secure Role-Based Access Control (RBAC)
-  Medical Records Management
-  Pharmacy Inventory & Prescription Management
- Neo4j Graph Analytics for healthcare relationship modeling
-  Sarvam AI for intelligent clinical decision support
-  Expo-powered cross-platform mobile application
-  FastAPI backend with React frontend

Together, these technologies create a scalable, intelligent, and modern healthcare platform capable of delivering smarter insights and improved patient care.
