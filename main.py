import json
import os

import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

REGION = os.getenv("AWS_REGION", "eu-west-1")
MODEL_ID = os.getenv("MODEL_ID", "mistral.mistral-large-2402-v1:0")

client = boto3.client(
    service_name="bedrock-runtime",
    region_name=REGION,
)

prompt = """
Tu es un assistant de navigation web pour personnes malvoyantes.
Réponds en une phrase simple.

Question : Que peux-tu faire pour aider un utilisateur sur une page web ?
"""

body = {
    "prompt": f"<s>[INST] {prompt} [/INST]",
    "max_tokens": 200,
    "temperature": 0.2,
}

try:
    response = client.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())
    print(response_body)

except ClientError as e:
    print("Erreur Bedrock :")
    print(e)