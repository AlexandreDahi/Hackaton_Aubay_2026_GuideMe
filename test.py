import sounddevice as sd
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel
import os
import Json
DUREE = 5          # secondes d'enregistrement
SAMPLE_RATE = 16000
FICHIER = "audio.wav"


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
    for segment in segments:
        print(segment.text)
    print("=========================")

if __name__ == "__main__":
    enregistrer()
    transcrire()