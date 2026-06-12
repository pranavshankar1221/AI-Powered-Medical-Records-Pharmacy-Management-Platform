# MEDIQR MLOPS

AI-Powered Pharmacy Inventory, Billing, Patient Guidance, and Analytics Platform.

## Project Overview
MEDIQR is a comprehensive web application designed to bridge the gap between B2B pharmacy operations and B2C patient interactions, enhanced with AI capabilities and MLOps practices.

### Features
1. **Inventory Management & ML Forecasting:** Uses `RandomForest` models to predict stock demand and expiry risks.
2. **Smart Billing & QR Generation:** Generates cryptographically signed QR codes on invoices for instant digital prescriptions.
3. **Patient Companion (AI Chatbot):** Patients scan their receipt QR codes to get AI-generated insights, dosage instructions, and interactions using LLMs.
4. **MLOps Dashboard:** Embedded monitoring using MLFlow, Prometheus, and Grafana for model drift and system health.

---

## 🚀 Local Development Workflow

### Prerequisites
- Docker & Docker Compose
- Node.js (for local frontend dev without Docker)
- Python 3.10+ (for local backend dev without Docker)

### 1. Environment Setup
```bash
# Copy example env files
cp .env.example .env
cp backend/.env.example backend/.env # If applicable

# Fill in your GEMINI_API_KEY in the backend/.env file to enable the AI Explainer.
```

### 2. Running Locally (Without Docker)

**Backend (FastAPI):**
1. Open a terminal and navigate to the `backend` directory.
2. Create and activate a Python virtual environment:
   ```bash
   cd backend
   python -m venv venv
   # On Windows: venv\Scripts\activate
   # On Mac/Linux: source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the backend server:
   ```bash
   python main.py
   # API will be available at http://localhost:8000
   ```

**Frontend (React/Vite):**
1. Open a new terminal and navigate to the `frontend` directory.
2. Install Node dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   # App will be available at the URL shown in the terminal (e.g., http://localhost:5173)
   ```

### 3. Running with Docker Compose (Recommended)
This will spin up the MySQL database, Backend (FastAPI), Frontend (React/Vite), MLFlow, Prometheus, and Grafana.

```bash
docker-compose up --build -d
```

- **Frontend Application:** [http://localhost:80](http://localhost:80)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **MLFlow UI:** [http://localhost:5001](http://localhost:5001)
- **Prometheus:** [http://localhost:9090](http://localhost:9090)
- **Grafana:** [http://localhost:3000](http://localhost:3000)

---

## 🐳 Docker Hub Push Workflow

We provide a script to automatically build and push the frontend and backend images to Docker Hub.

```bash
# Make the script executable
chmod +x scripts/docker_push.sh

# Run the script with your Docker Hub username
./scripts/docker_push.sh <your_dockerhub_username>
```

---

## ☁️ AWS Deployment Workflow (ECR / ECS Fargate)

To deploy the MEDIQR platform to AWS, follow this workflow using AWS Elastic Container Registry (ECR) and Elastic Container Service (ECS).

### Prerequisites
- AWS CLI installed and configured (`aws configure`)
- IAM User with permissions for ECR and ECS.

### Step 1: Push Images to AWS ECR
Create ECR repositories and push your images.

```bash
# 1. Create ECR repositories
aws ecr create-repository --repository-name mediqr-backend
aws ecr create-repository --repository-name mediqr-frontend

# 2. Authenticate Docker to your Amazon ECR registry
aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <your-account-id>.dkr.ecr.<your-region>.amazonaws.com

# 3. Tag your local images
docker tag <your_dockerhub_username>/mediqr-backend:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/mediqr-backend:latest
docker tag <your_dockerhub_username>/mediqr-frontend:latest <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/mediqr-frontend:latest

# 4. Push images to ECR
docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/mediqr-backend:latest
docker push <your-account-id>.dkr.ecr.<your-region>.amazonaws.com/mediqr-frontend:latest
```

### Step 2: Set up AWS RDS (MySQL)
Instead of running a MySQL container in ECS, it is recommended to use **Amazon RDS for MySQL** for production.
1. Create a MySQL RDS instance in the AWS Console.
2. Note the endpoint URL, username, and password.
3. Set your backend container's `DATABASE_URL` environment variable to point to this RDS instance.

### Step 3: Create ECS Cluster and Task Definitions
1. **Create an ECS Cluster** using AWS Fargate.
2. **Create Task Definition** for the Backend:
   - Image: `<your-account-id>.dkr.ecr.<your-region>.amazonaws.com/mediqr-backend:latest`
   - Port Mapping: `8000`
   - Environment Variables:
     - `DATABASE_URL` = `mysql+pymysql://<user>:<pass>@<rds-endpoint>:3306/<dbname>`
     - `GEMINI_API_KEY` = `<your-api-key>`
3. **Create Task Definition** for the Frontend:
   - Image: `<your-account-id>.dkr.ecr.<your-region>.amazonaws.com/mediqr-frontend:latest`
   - Port Mapping: `80`

### Step 4: Run ECS Services
1. Create a Service in your ECS Cluster for the Backend Task. Set up an Application Load Balancer (ALB) to expose port 8000.
2. Create a Service for the Frontend Task. Set up another ALB (or route on the same ALB) to expose port 80.
3. Ensure the Frontend connects to the Backend's ALB endpoint.

*Your MEDIQR application is now running securely on AWS!*
