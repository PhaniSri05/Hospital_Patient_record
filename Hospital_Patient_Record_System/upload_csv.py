import requests

url = "http://127.0.0.1:5000/api/reports/upload"

token = input("Paste your admin JWT token: ")

headers = {
    "Authorization": f"Bearer {token}"
}

with open("sample_appointments.csv", "rb") as file:
    response = requests.post(
        url,
        headers=headers,
        files={
            "file": (
                "sample_appointments.csv",
                file,
                "text/csv"
            )
        }
    )

print("Status:", response.status_code)
print("Response:", response.text)