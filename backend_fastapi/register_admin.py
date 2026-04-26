import requests

url = "http://127.0.0.1:8000/api/v1/auth/register"
data = {
    "email": "superadmin2@kalsel.com",
    "username": "superadmin2",
    "password": "password123"
}

try:
    # FastAPI is expecting query parameters because we didn't use a Pydantic model for the request body
    response = requests.post(url, params=data)
    if response.status_code == 201:
        print("✅ SUCCESS: Akun berhasil dibuat!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ FAILED: Gagal membuat akun. Status: {response.status_code}")
        print(f"Error detail: {response.text}")
except Exception as e:
    print(f"Koneksi error: {e}")
