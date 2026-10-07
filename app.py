import requests
from fastapi import FastAPI
import re

app = FastAPI(
    title="SMEBOT"
)


@app.get("/")
def home():
    return {"message": "SMEBOT"}


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


def is_valid_vin(vin: str):

    pattern = r"^[A-HJ-NPR-Z0-9]{17}$"

    return bool(
        re.match(pattern, vin.upper())
    )
    

@app.get("/vin/{vin}")
def decode_vin(vin: str):

    if not is_valid_vin(vin):
        return {
            "error": "Invalid VIN"
        }
        
    url = (
        f"https://vpic.nhtsa.dot.gov/api/"
        f"vehicles/DecodeVinValues/"
        f"{vin}?format=json"
    )

    response = requests.get(url)

    data = response.json()

    result = data["Results"][0]

    if not result["Make"]:
        return {
        "error": "VIN could not be decoded"
        }    
        
    return {
        "vin": vin,
        "year": result["ModelYear"],
        "make": result["Make"],
        "model": result["Model"]
    }