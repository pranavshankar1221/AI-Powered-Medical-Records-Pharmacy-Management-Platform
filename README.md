# MEDIQR MLOps

## AI-Powered Pharmacy Inventory, Billing, Patient Guidance & MLOps Platform

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![React](https://img.shields.io/badge/React-Frontend-blue)
![MySQL](https://img.shields.io/badge/MySQL-Database-orange)
![MLflow](https://img.shields.io/badge/MLflow-MLOps-purple)
![Docker](https://img.shields.io/badge/Docker-Containerization-blue)

---

# Project Overview

MEDIQR is a next-generation pharmacy management ecosystem that combines inventory management, QR-based billing, patient medicine guidance, machine learning forecasting, AI-powered medicine assistance, and MLOps practices into a single platform.

The system bridges the gap between:

* Pharmacy Operations (B2B)
* Patient Healthcare Assistance (B2C)

while implementing industry-standard MLOps workflows for model training, deployment, monitoring, and reproducibility.

---

# Problem Statement

Pharmacies face several challenges:

### Inventory Issues

* Manual stock management
* Stock shortages
* Overstocking
* Expired medicines remaining unnoticed

### Billing Issues

* Lack of patient engagement after billing
* No digital medicine tracking

### Patient Issues

Patients often do not know:

* Purpose of medicines
* Side effects
* Dosage timing
* Food restrictions

### Business Issues

* Poor inventory forecasting
* Revenue loss due to expired stock
* Inefficient stock replenishment

---

# Proposed Solution

MEDIQR provides:

### Smart Inventory Management

* Medicine stock tracking
* Batch management
* Expiry monitoring
* Low-stock alerts

### Smart Billing System

* Digital billing
* Secure QR generation
* Automatic stock deduction

### Patient Companion

* QR-based medicine access
* Medicine purpose explanation
* Dosage instructions
* Reminder system

### AI & Machine Learning

* Demand forecasting
* Expiry risk prediction
* AI medicine assistant
* RAG-powered medicine guidance

### MLOps Pipeline

* MLflow
* DVC
* Docker
* Prometheus
* Grafana

---

# Key Features

## Pharmacy Side

### Inventory Management

* Add medicines
* Update stock
* Delete medicines
* Batch tracking
* Expiry tracking

### Billing System

* Generate bills
* Calculate totals
* Reduce inventory automatically
* Generate QR receipts

### Analytics Dashboard

* Sales analytics
* Inventory reports
* Demand forecasts
* Expiry alerts

---

## Patient Side

### QR Scan

Patient scans QR from bill.

Displays:

* Medicine name
* Purpose
* Dosage instructions
* Side effects
* Food instructions
* Billing amount

### Reminder System

* Morning reminders
* Afternoon reminders
* Evening reminders
* Custom reminders

### AI Assistant

Patients can ask:

* What is this medicine used for?
* What are its side effects?
* When should I take it?

The assistant only provides verified information and never changes prescriptions.

---

# System Architecture

```text
                 React Frontend
                        │
                        ▼
                 FastAPI Backend
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼

     MySQL DB      ML Services     QR Services

        ▼               ▼               ▼

   Inventory       Demand Model     QR Billing
   Billing         Expiry Model     QR Scanner
```

---

#  User Roles

## Admin

* Manage users
* View analytics
* Monitor system

## Pharmacist

* Manage inventory
* Create bills
* Generate QR receipts
* View stock forecasts

## Patient

* Scan QR bills
* View medicine details
* Create reminders
* Use AI assistant

---

# Technology Stack

| Layer               | Technology       |
| ------------------- | ---------------- |
| Frontend            | React + Vite     |
| Backend             | FastAPI          |
| Database            | MySQL            |
| Authentication      | JWT              |
| ORM                 | SQLAlchemy       |
| QR Generation       | qrcode           |
| QR Scanner          | React QR Scanner |
| ML                  | Scikit-Learn     |
| Experiment Tracking | MLflow           |
| Dataset Versioning  | DVC              |
| Monitoring          | Prometheus       |
| Visualization       | Grafana          |
| Containerization    | Docker           |
| Deployment          | AWS ECS Fargate  |

---

# Database Design

## Users

```sql
id
name
email
password_hash
role
created_at
```

## Medicines

```sql
id
medicine_name
batch_number
manufacturer
category
quantity
price_per_unit
expiry_date
purpose
dosage_instruction
side_effects
food_instruction
```

## Bills

```sql
id
bill_number
bill_token
patient_name
patient_phone
total_amount
created_at
```

## Bill Items

```sql
id
bill_id
medicine_id
quantity
unit_price
subtotal
```

## Reminders

```sql
id
patient_id
medicine_id
reminder_time
reminder_type
status
```

---

# Secure QR Workflow

### Why Store Only Bill Token?

Instead of storing:

```json
{
  "medicine":"Paracetamol",
  "amount":120
}
```

Store:

```json
{
  "bill_token":"abc123xyz"
}
```

Benefits:

* Secure
* Lightweight
* Scalable
* Tamper-resistant

Workflow:

```text
Bill Generated
      ↓
QR Contains Bill Token
      ↓
Patient Scans QR
      ↓
Backend Validates Token
      ↓
Medicine Information Displayed
```

---

# Machine Learning Modules

## Demand Forecasting

### Goal

Predict medicine demand for the next 30 days.

### Features

* Past sales
* Current stock
* Category
* Month
* Season
* Expiry days remaining

### Model

```python
RandomForestRegressor
```

### Output

```text
Predicted Demand = 450 Units
```

---

## Expiry Risk Prediction

### Goal

Predict medicine batches likely to expire before sale.

### Model

```python
RandomForestClassifier
```

### Output

```text
LOW
MEDIUM
HIGH
```

---

# MLOps Workflow

```text
Sales Data
     ↓
DVC Versioning
     ↓
Feature Engineering
     ↓
Model Training
     ↓
MLflow Tracking
     ↓
Model Registry
     ↓
Deployment
     ↓
Monitoring
```

---

# Monitoring & Observability

## Prometheus

Collects:

* API latency
* Request count
* Error rate
* CPU usage
* Memory usage

## Grafana

Visualizes:

* User activity
* Inventory trends
* Model metrics
* System health

---

#  AI Assistant & RAG

Workflow:

```text
Patient Query
      ↓
Embedding Model
      ↓
FAISS Search
      ↓
Relevant Medicine Context
      ↓
Gemini API
      ↓
Safe Response
```

Safety Rules:

* No diagnosis
* No prescription changes
* No dosage modifications

---

# API Documentation

## Authentication

```http
POST /auth/register
POST /auth/login
```

## Medicines

```http
GET /medicines
POST /medicines
PUT /medicines/{id}
DELETE /medicines/{id}
```

## Billing

```http
POST /billing/create
GET /billing/{id}
```

## Patient

```http
GET /patient/bill/{token}
POST /patient/reminders
GET /patient/reminders
```

## Machine Learning

```http
GET /ml/predict-demand/{id}
GET /ml/expiry-risk/{id}
```

---

# Project Structure

```text
mediqr-mlops/
│
├── backend/
│   ├── app/
│   ├── routes/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── ml/
│   └── utils/
│
├── frontend/
│   ├── pages/
│   ├── components/
│   └── services/
│
├── mlops/
│   ├── data/
│   ├── models/
│   ├── training/
│   └── dvc.yaml
│
├── docker-compose.yml
└── README.md
```

---

# Local Setup

## Backend

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

#  Docker Setup

```bash
docker-compose up --build
```

Services:

* MySQL
* FastAPI
* React
* MLflow
* Prometheus
* Grafana

---

# End-to-End Testing

### Pharmacy Workflow

1. Login as Pharmacist
2. Add Medicine Stock
3. Verify Inventory
4. View Expiry Alerts
5. Create Bill
6. Generate QR

### Patient Workflow

7. Scan QR
8. View Medicine Details
9. Set Reminder

### ML Workflow

10. Predict Demand
11. Predict Expiry Risk
12. Verify MLflow Tracking
13. Verify Grafana Dashboard

---

# Security Features

* JWT Authentication
* Password Hashing
* Role-Based Access Control
* Secure QR Tokens
* API Validation
* Environment Variables
* HMAC Verification

---

# AWS Deployment

Services:

* Amazon ECS Fargate
* Amazon RDS MySQL
* Application Load Balancer
* Amazon ECR

Deployment Flow:

```text
Developer
    ↓
GitHub
    ↓
Docker Build
    ↓
AWS ECR
    ↓
ECS Fargate
    ↓
Production
```

---

# Team Contributions

## Member 1

Backend Development

* FastAPI
* MySQL
* Authentication
* Billing APIs

## Member 2

Frontend Development

* React UI
* QR Scanner
* Patient Dashboard

## Member 3

ML & MLOps

* Demand Forecasting
* Expiry Prediction
* MLflow
* DVC
* Monitoring

---

# Future Enhancements

* OCR Prescription Reading
* Voice-Based Medicine Guidance
* Multi-Language Support
* WhatsApp Reminder Bot
* Blockchain Supply Chain Tracking
* IoT Smart Medicine Cabinets

---

# Key Technical Achievements

* Full Stack Development
* REST API Design
* JWT Authentication
* QR Integration
* Machine Learning Deployment
* MLOps Implementation
* Docker Containerization
* Cloud Deployment Ready
* Monitoring & Observability

---

# Disclaimer

This platform provides medicine information only for educational and awareness purposes.

Patients must always follow their doctor's prescription.

The AI assistant never diagnoses diseases, modifies prescriptions, or recommends dosage changes.

---

# Conclusion

MEDIQR bridges the gap between pharmacy inventory management and patient healthcare assistance through AI, QR technology, predictive analytics, and production-grade MLOps practices.

The platform improves pharmacy efficiency, reduces medicine wastage, enhances patient awareness, and demonstrates real-world deployment-ready machine learning workflows.
