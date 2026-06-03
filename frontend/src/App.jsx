import { useState } from "react";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [assistantMessage, setAssistantMessage] = useState("");

  function normalizeText(value) {
    return value
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

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
      handleUserRequest(transcript);
    };

    recognition.onerror = (event) => {
      console.error(event.error);
      alert(`Erreur micro : ${event.error}`);
    };

    recognition.start();
  }

  function speak(message) {
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(message);
    utterance.lang = "fr-FR";
    utterance.rate = 0.95;

    window.speechSynthesis.speak(utterance);
  }

  async function handleUserRequest(request) {
  const pageContext = [
    {
      id: "contracts",
      role: "section",
      text: "Mes contrats",
      description: "Consulter les garanties et options"
    },
    {
      id: "refunds",
      role: "button",
      text: "Voir mes remboursements",
      description: "Voir les paiements récents et remboursements en attente"
    },
    {
      id: "attestation",
      role: "button",
      text: "Télécharger mon attestation",
      description: "Récupérer une attestation ou un justificatif"
    },
    {
      id: "personal-info",
      role: "section",
      text: "Mes informations personnelles",
      description: "Contient l'adresse actuelle de l'utilisateur"
    },
    {
      id: "edit-address",
      role: "button",
      text: "Modifier",
      description: "Modifier l'adresse actuelle"
    },
    {
      id: "support",
      role: "button",
      text: "Contacter le support",
      description: "Demander de l'aide à un conseiller"
    }
  ];

  const response = await fetch("http://localhost:8000/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_request: request,
      page_context: pageContext,
    }),
  });

  const data = await response.json();

  setAssistantMessage(data.message);
  speak(data.message);
}

  return (
    <main className="app">
      <section className="assistant-panel" aria-label="Assistant GuideMe">
        <h1>GuideMe</h1>
        <p>
          Assistant vocal de navigation pour personnes aveugles ou malvoyantes.
        </p>

        <button className="voice-button" onClick={startVoiceRecognition}>
          🎤 Parler
        </button>

        <button onClick={() => handleUserRequest("Je viens de déménager")}>
          Démo : “Je viens de déménager”
        </button>

        <button onClick={() => handleUserRequest("Je veux mon attestation")}>
          Démo : “Je veux mon attestation”
        </button>

        <button onClick={() => speak("Bonjour, la voix GuideMe fonctionne.")}>
          🔊 Tester la voix
        </button>

        <div className="result-box" aria-live="polite">
          <p>
            <strong>Texte reconnu :</strong> {text || "Aucune commande"}
          </p>
          <p>
            <strong>GuideMe :</strong> {assistantMessage || "En attente..."}
          </p>
        </div>
      </section>

      <section className="fake-site" aria-label="Fausse page de mutuelle">
        <header className="bad-header">
          <h2>Mutuelle Santé Plus</h2>
          <nav>
            <button>Accueil</button>
            <button>Mes infos</button>
            <button>Mon espace</button>
            <button>Aide</button>
            <button>Paramètres</button>
          </nav>
        </header>

        <div className="warning">
          Information importante : certains services sont temporairement
          indisponibles. Pour toute demande, veuillez accéder à votre espace.
        </div>

        <div className="grid">
          <section className="card">
            <h3>Mes contrats</h3>
            <p>Retrouvez vos garanties, options et informations générales.</p>
            <button>Voir</button>
            <button>Consulter</button>
            <button>Gérer</button>
          </section>

          <section className="card">
            <h3>Mes remboursements</h3>
            <p>
              Consultez les remboursements récents et les paiements en attente.
            </p>
            <button>Voir mes remboursements</button>
            <button>Historique</button>
            <button>Détails</button>
          </section>

          <section className="card">
            <h3>Mes documents</h3>
            <p>Documents, justificatifs, attestations et courriers.</p>
            <button>Ouvrir</button>
            <button>Télécharger mon attestation</button>
            <button>Archives</button>
          </section>

          <section className="card confusing-card">
            <h3>Mes informations personnelles</h3>
            <p>Adresse actuelle : 15 rue des Lilas, 69003 Lyon</p>
            <button>Voir</button>
            <button>Modifier</button>
            <button>Accéder</button>
          </section>

          <section className="card">
            <h3>Support</h3>
            <p>Contactez un conseiller ou envoyez une demande.</p>
            <button>Contact</button>
            <button>Message</button>
            <button>Assistance</button>
          </section>

          <section className="card">
            <h3>Notifications</h3>
            <p>Vous avez 4 messages non lus et 2 documents à vérifier.</p>
            <button>Lire</button>
            <button>Plus tard</button>
            <button>Tout voir</button>
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;