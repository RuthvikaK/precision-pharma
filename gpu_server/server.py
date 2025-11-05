"""GPU Server - Optional GPU acceleration for advanced ML models"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import torch

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check GPU availability
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "online",
        "device": DEVICE,
        "gpu_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
    }

@app.post("/predict")
async def predict(data: dict):
    """
    Optional GPU-accelerated predictions
    Could be used for advanced ML models predicting drug response
    """
    # Placeholder for ML model inference
    return {
        "status": "success",
        "device_used": DEVICE,
        "message": "GPU server ready for ML inference"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)