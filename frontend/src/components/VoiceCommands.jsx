import { useEffect, useRef, useState } from "react";

const COMMAND_KEYWORDS = {
  SCAN: ["scan", "scanning", "start scan"],
  GUIDE: ["guide", "guidance"],
  SELECT: ["select", "choose", "object", "select object"],
  READ: ["read", "read text", "read it"],
};

function VoiceCommands({ onCommand, isEnabled }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [lastCommand, setLastCommand] = useState("");
  const recognitionRef = useRef(null);
  const lastCommandTime = useRef(0);

  useEffect(() => {
    if (!isEnabled) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.error("Speech Recognition not supported in this browser");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      console.log("Voice recognition started");
      setIsListening(true);
    };

    recognition.onend = () => {
      console.log("Voice recognition ended");
      setIsListening(false);
      if (isEnabled) {
        setTimeout(() => {
          try {
            recognition.start();
          } catch (e) {
            console.log("Recognition restart failed:", e);
          }
        }, 100);
      }
    };

    recognition.onerror = (event) => {
      console.error("Voice recognition error:", event.error);
      if (event.error === "no-speech") {
        return;
      }
      setIsListening(false);
    };

    recognition.onresult = (event) => {
      const last = event.results.length - 1;
      const text = event.results[last][0].transcript.toLowerCase().trim();

      console.log("Voice heard:", text);
      setTranscript(text);

      const command = resolveCommand(text);
      if (command) {
        const now = Date.now();
        if (now - lastCommandTime.current > 2500) {
          console.log("Command resolved:", command);
          setLastCommand(command);
          onCommand(command);
          lastCommandTime.current = now;
        }
      }
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (e) {
      console.error("Failed to start recognition:", e);
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isEnabled, onCommand]);

  const resolveCommand = (text) => {
    for (const [command, keywords] of Object.entries(COMMAND_KEYWORDS)) {
      for (const keyword of keywords) {
        if (text.includes(keyword)) {
          return command;
        }
      }
    }
    return null;
  };

  return (
    <div className="voice-commands">
      <h3>Voice Commands</h3>
      <div
        className={`voice-status ${
          isListening ? "listening" : "not-listening"
        }`}
      >
        <div className="voice-indicator">
          {isListening ? "Listening..." : "Not Listening"}
        </div>
      </div>

      {transcript && (
        <div className="voice-transcript">
          <strong>Heard:</strong> "{transcript}"
        </div>
      )}

      {lastCommand && (
        <div className="voice-last-command">
          <strong>Last Command:</strong> {lastCommand}
        </div>
      )}

      <div className="voice-keywords">
        <h4>Say these words:</h4>
        <div className="keyword-list">
          <span className="keyword-badge">scan</span>
          <span className="keyword-badge">guide</span>
          <span className="keyword-badge">select</span>
          <span className="keyword-badge">read</span>
        </div>
      </div>
    </div>
  );
}

export default VoiceCommands;
