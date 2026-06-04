import sounddevice as sd
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel
import os
import json
DUREE = 5          # secondes d'enregistrement
SAMPLE_RATE = 16000
FICHIER = "audio.wav"
TRANSCRIPT_JSON = "transcript.json"


def enregistrer():
    print(f"🎙️  Parlez maintenant... ({DUREE} secondes)")
    audio = sd.rec(
        int(DUREE * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )
    sd.wait()  # attend la fin de l'enregistrement
    sf.write(FICHIER, audio, SAMPLE_RATE)
    print(f"✅  Enregistrement terminé -> {FICHIER}")

def transcrire():
    print("🔄  Transcription en cours...")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    segments, info = model.transcribe(FICHIER, language="fr")
    print(f"📝  Langue détectée : {info.language} (confiance : {info.language_probability:.0%})")
    print("\n===== TRANSCRIPTION =====")
    transcript_data = []
    for segment in segments:
        print(segment.text)
        transcript_data.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
    print("=========================")

    with open(TRANSCRIPT_JSON, "w", encoding="utf-8") as f:
        json.dump({
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": transcript_data
        }, f, ensure_ascii=False, indent=2)

    print(f"✅  Transcription sauvegardée dans {TRANSCRIPT_JSON}")

if __name__ == "__main__":
    enregistrer()
    transcrire()