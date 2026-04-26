import requests

url = "http://127.0.0.1:8000/api/v1/auth/login"
data = {"username": "superadmin2", "password": "password123"}
try:
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("LOGIN BERHASIL!")
        print(response.json())
    else:
        print("LOGIN GAGAL!")
        print(response.status_code, response.text)
except Exception as e:
    print(e)
