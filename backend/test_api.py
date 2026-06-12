import requests

# We need a token first
auth_res = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "admin123"}
)

if auth_res.status_code != 200:
    print("Login failed:", auth_res.text)
    exit(1)

token = auth_res.json()["access_token"]

med_data = {
    "name": "Test Med",
    "generic_name": "",
    "category": "Test",
    "manufacturer": "",
    "dosage_form": "",
    "strength": "",
    "unit_price": 10.0,
    "description": "",
    "purpose": "",
    "dosage_schedule": ""
}

headers = {"Authorization": f"Bearer {token}"}
res = requests.post("http://localhost:8000/api/inventory/medicines", json=med_data, headers=headers)
print("STATUS:", res.status_code)
print("BODY:", res.text)
