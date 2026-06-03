import { useState } from "react";

function App() {
  const [text, setText] = useState("");

  function startVoiceRecognition() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Reconnaissance vocale non supportée.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "fr-FR";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setText(transcript);
      speak(`Vous avez dit : ${transcript}`);
    };

    recognition.onerror = (event) => {
      console.error(event.error);
      alert(`Erreur micro : ${event.error}`);
    };

    recognition.start();
  }

  function speak(message) {
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.lang = "fr-FR";
    window.speechSynthesis.speak(utterance);
  }

  return (
    <main style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>Test voix GuideMe</h1>

      <button onClick={startVoiceRecognition}>
        🎤 Parler
      </button>

      <button onClick={() => speak("Bonjour Louis, la voix fonctionne.")}>
        🔊 Tester la voix
      </button>

      <p>
        <strong>Texte reconnu :</strong> {text}
      </p>
    </main>
  );
}

export default App;