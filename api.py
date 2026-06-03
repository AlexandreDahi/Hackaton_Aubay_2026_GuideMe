import json
import os

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_REGION", "eu-west-1")
MODEL_ID = os.getenv("MODEL_ID", "mistral.mistral-large-2402-v1:0")

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PageElement(BaseModel):
    id: str
    role: str
    text: str
    description: str | None = None


class AnalyzeRequest(BaseModel):
    user_request: str
    page_context: list[PageElement]


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    prompt = f"""
Tu es GuideMi , un assistant vocal pour personnes aveugles ou malvoyantes.

Contexte :
L'utilisateur navigue sur une page web complexe.
Il ne voit pas l'écran.
Tu dois l'aider à comprendre où aller.

Ton rôle :
- comprendre l'intention réelle de l'utilisateur, même si sa phrase ne correspond pas exactement aux textes de la page ;
- choisir l'élément de page le plus utile ;
- expliquer oralement pourquoi cet élément est pertinent ;
- rester court, clair et rassurant.

Demande de l'utilisateur :
"{request.user_request}"

Éléments disponibles sur la page :
{json.dumps([e.model_dump() for e in request.page_context], ensure_ascii=False, indent=2)}

Règles :
- Si l'utilisateur dit qu'il a déménagé, il veut probablement modifier son adresse.
- Si l'utilisateur parle d'attestation, de justificatif ou de document, il veut probablement accéder aux documents.
- Si l'utilisateur parle de remboursement, il veut probablement consulter ses remboursements.
- Ne dis jamais que tu as "surligné" un élément.
- Ne parle pas d'interface visuelle.
- Réponds comme si tu parlais à une personne aveugle.

Réponds uniquement en JSON valide, sans markdown :
{{
  "target_id": "id de l'élément le plus pertinent ou null",
  "message": "réponse courte à lire à voix haute"
}}
"""

    body = {
        "prompt": f"<s>[INST] {prompt} [/INST]",
        "max_tokens": 250,
        "temperature": 0.1,
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    result = json.loads(response["body"].read())
    text = result["outputs"][0]["text"].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "target_id": None,
            "message": text,
        }