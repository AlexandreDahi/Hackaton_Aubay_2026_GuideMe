import json
import os

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

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
    page_url: str | None = None
    page_context: list[PageElement] | None = None


def extract_page_context(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        elements = page.locator("button, a, input, textarea, select").evaluate_all("""
        els => els.map((el, index) => {
            const id = el.id || el.getAttribute("data-guideme-id") || `auto-${index}`;
            if (!el.id && !el.getAttribute("data-guideme-id")) {
                el.setAttribute("data-guideme-id", id);
            }

            return {
                id: id,
                role: el.tagName.toLowerCase(),
                text:
                    el.innerText ||
                    el.value ||
                    el.getAttribute("aria-label") ||
                    el.getAttribute("placeholder") ||
                    "",
                description:
                    el.getAttribute("title") ||
                    el.getAttribute("name") ||
                    ""
            };
        })
        """)
        print("=== PLAYWRIGHT ELEMENTS ===")
        print(json.dumps(elements, indent=2, ensure_ascii=False))
        browser.close()
        return elements


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    if request.page_context:
        page_context = [e.model_dump() for e in request.page_context]
    elif request.page_url:
        page_context = extract_page_context(request.page_url)
    else:
        return {
            "target_id": None,
            "message": "Aucun contexte de page n'a été fourni."
        }

    prompt = f"""
Tu es GuideMe, un assistant vocal pour personnes aveugles ou malvoyantes.

Contexte :
L'utilisateur navigue sur une page web complexe.
Il ne voit pas l'écran.
Tu dois l'aider à comprendre où aller.

Ton rôle :
- comprendre l'intention réelle de l'utilisateur, même si sa phrase ne correspond pas exactement aux textes de la page ;
- choisir l'élément de page le plus utile ;
- expliquer oralement pourquoi cet élément est pertinent ;
- rester court, clair et rassurant.

Réponds uniquement et obligatoirement en JSON dans le format suivant, sans markdown :
{{
"message": "réponse courte à lire à voix haute",
  "target_id": "id de l'élément le plus pertinent ou null"
}}

Demande de l'utilisateur :
"{request.user_request}"

Éléments disponibles sur la page :
{json.dumps(page_context, ensure_ascii=False, indent=2)}

Règles :
- Si l'utilisateur dit qu'il a déménagé, il veut probablement modifier son adresse.
- Si l'utilisateur parle d'attestation, de justificatif ou de document, il veut probablement accéder aux documents.
- Si l'utilisateur parle de remboursement, il veut probablement consulter ses remboursements.
- Ne dis jamais que tu as "surligné" un élément.
- Ne parle pas d'interface visuelle.
- Réponds comme si tu parlais à une personne aveugle.


"""

    body = {
        "prompt": f"<s>[INST] {prompt} [/INST]",
        "max_tokens": 500,
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

    print("=== PAGE CONTEXT ===")
    print(json.dumps(page_context, ensure_ascii=False, indent=2))

    print("=== BEDROCK RAW RESPONSE ===")
    print(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "target_id": None,
            "message": text,
        }   