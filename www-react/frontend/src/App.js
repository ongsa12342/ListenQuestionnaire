// App.js
import React, { useState } from "react";
import Questionnaire from "./Questionnaire";
import LandingPage from "./LandingPage"; // Ensure this is the updated file

function App() {
  const [participantName, setParticipantName] = useState("");
  const sequenceId = 5; // Set your sequenceId accordingly

  return (
    <>
      {participantName === "" ? (
        <LandingPage onStart={(name) => setParticipantName(name)} />
      ) : (
        <Questionnaire sequenceId={sequenceId} participantName={participantName} />
      )}
    </>
  );
}

export default App;
