import json
import os

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from datetime import datetime

load_dotenv()

REGION = os.getenv("AWS_REGION", "eu-west-1")
MODEL_ID = os.getenv("MODEL_ID", "mistral.mistral-large-2402-v1:0")

pending_action = None
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

def save_response(user_request: str, bedrock_response: dict):
    """Sauvegarde la question et la réponse de bedrock dans un fichier JSON"""
    # Créer le répertoire 'réponse' s'il n'existe pas
    response_dir = "réponse"
    os.makedirs(response_dir, exist_ok=True)
   
    # Créer un timestamp pour le nom du fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # avec millisecondes
    filename = os.path.join(response_dir, f"response_{timestamp}.json")
   
    # Créer le dictionnaire avec la question et la réponse
    data = {
        "timestamp": datetime.now().isoformat(),
        "user_request": user_request,
        "bedrock_response": bedrock_response
    }
   
    # Sauvegarder le JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
   
    print(f"Response saved to {filename}")

def extract_page_context(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        elements = page.locator("button, a, input, textarea, select").evaluate_all("""
        els => els.map((el, index) => {
            const id = el.getAttribute("data-guideme-id") || el.id || `auto-${index}`;

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

        browser.close()

        cleaned_elements = [
            element for element in elements
            if element.get("text", "").strip() or element.get("description", "").strip()
        ]

        return cleaned_elements[:50]

def normalize_user_request(value: str) -> str:
    return (
        value.lower()
        .strip()
        .replace(".", "")
        .replace(",", "")
        .replace("!", "")
        .replace("?", "")
    )

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    global pending_action
    normalized_request = normalize_user_request(request.user_request)
    if request.page_context:
        page_context = [element.model_dump() for element in request.page_context]
    elif request.page_url:
        page_context = extract_page_context(request.page_url)
    else:
        return {
            "target_id": None,
            "requires_confirmation": False,
            "message": "Aucun contexte de page n'a été fourni."
        }
    confirmation_words = [
        "oui",
        "ok",
        "vas y",
        "vas-y",
        "continue",
        "confirmer",
        "je confirme",
        "daccord",
        "d'accord",
        "allez",
    ]
    print("REQUEST =", request.user_request)
    print("NORMALIZED =", normalized_request)
    print("PENDING =", pending_action)
    if pending_action and any(
        word in normalized_request
        for word in confirmation_words
    ):
        action = pending_action
        pending_action = None

        return {
            "message": "Confirmation reçue. Je vais poursuivre cette action.",
            "target_id": action,
            "confirmed": True,
            "requires_confirmation": False
        }
    prompt = f"""
Tu es GuideMe, un assistant vocal pour personnes aveugles ou malvoyantes.

Contexte :
L'utilisateur navigue sur une page web complexe.
Il ne voit pas l'écran.
Tu dois l'aider à atteindre son objectif sans lui imposer de parcourir toute l'interface.

Ton rôle :
- comprendre l'intention réelle de l'utilisateur, même si sa phrase ne correspond pas exactement aux textes de la page ;
- choisir l'élément de page le plus utile ;
- expliquer oralement pourquoi cet élément semble pertinent ;
- demander une confirmation avant toute action ;
- rester court, clair et rassurant.

Demande de l'utilisateur :
"{request.user_request}"

Éléments disponibles sur la page :
{json.dumps(page_context, ensure_ascii=False, indent=2)}

Règles de décision :
- Si l'utilisateur dit qu'il a déménagé, il veut probablement modifier son adresse.
- Si l'utilisateur parle d'attestation, de justificatif ou de document, il veut probablement accéder aux documents.
- Si l'utilisateur parle de remboursement, il veut probablement consulter ses remboursements.
- Si aucun élément pertinent n'est trouvé, target_id doit valoir null.
- Ne dis jamais que tu as "surligné" un élément.
- Ne parle pas d'interface visuelle.
- Réponds comme si tu parlais à une personne aveugle.
- Ne confirme jamais que l'action a été effectuée.
- Demande toujours le consentement avant d'ouvrir, cliquer, valider ou modifier quelque chose.

Format de réponse obligatoire attendu :
Choisi en envoyent le Json du cas 1 ou du cas 2,
Cas 1 l'utilisateur veut remplir un champ
Cas 2 l'utilisateur veut changer de page
Réponds uniquement en JSON valide, sans markdown, sans texte autour.
 
Cas 1
{{
  "message": "phrase courte à lire à voix haute, qui explique ce que tu veux faire",
  "cas": "1"
  "target_id": "id du champ le plus pertinent à remplir ou null",
}}
 
cas 2
{{
  "message": "phrase courte à lire à voix haute, qui explique ce que tu veux faire",
  "cas": "2"
  "target_id": "id du bouton le plus pertinent à cliquer ou null",
}}
 
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

    try:
        response_json = json.loads(text)
 
        if response_json.get("target_id"):
            pending_action = response_json["target_id"]
       
        # Sauvegarder la question et la réponse
        save_response(request.user_request, response_json)
 
        return response_json
    except json.JSONDecodeError:
        error_response = {
            "target_id": None,
            "requires_confirmation": False,
            "message": text,
        }
        # Sauvegarder même en cas d'erreur JSON
        save_response(request.user_request, error_response)
        return error_response