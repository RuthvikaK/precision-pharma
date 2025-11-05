from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from agents.orchestrator import OrchestratorAgent

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

orc = OrchestratorAgent()

class Req(BaseModel):
    drug: str
    indication: str
    use_gpu: bool = True

@app.post("/analyze")
async def analyze(r: Req):
    return orc.run(r.drug, r.indication, r.use_gpu)