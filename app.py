import requests
from fastapi import FastAPI
import re
from fastapi import UploadFile, File
from PIL import Image
import easyocr

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
  
    if not result.get("Make"):

        suggestions = generate_candidates(
            vin
        )

        match = try_candidates(
            suggestions
        )

        if match:

            return {
                "error": "VIN could not be decoded",
                "did_you_mean": match
            }

        return {
            "error": "VIN could not be decoded"
        }
    
    return {
        "vin": vin,
        "year": result["ModelYear"],
        "make": result["Make"],
        "model": result["Model"]
    }
    
    
reader = easyocr.Reader(["en"])

@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):

    contents = await file.read()

    with open("temp.jpg", "wb") as f:
        f.write(contents)

    result = reader.readtext(
        "temp.jpg",
        detail=0
    )

    return {
        "text": result
    }

OCR_CORRECTIONS = {
    "O": "0",
    "I": "1",
    "S": "5",
    "B": "8",
    "Z": "2",
    "Q": "0"
}

def generate_candidates(vin: str):

    candidates = []

    for bad, good in OCR_CORRECTIONS.items():

        if bad in vin:

            candidates.append(
                vin.replace(bad, good)
            )

def try_candidates(candidates):

    for candidate in candidates:

        url = (
            f"https://vpic.nhtsa.dot.gov/api/"
            f"vehicles/DecodeVinValues/"
            f"{candidate}?format=json"
        )

        response = requests.get(url)

        result = (
            response.json()["Results"][0]
        )

        if (
            result.get("Make")
            and result.get("Model")
        ):

            return {
                "suggested_vin": candidate,
                "make": result["Make"],
                "model": result["Model"],
                "year": result["ModelYear"]
            }

    return None

