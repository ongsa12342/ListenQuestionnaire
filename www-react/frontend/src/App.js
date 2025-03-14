// App.js
import React, { useState } from "react";
import Questionnaire from "./Questionnaire";
import LandingPage from "./LandingPage"; // Ensure this is the updated file


// import ReactDOM from "react-dom";
import "./i18n"; // Ensure this is imported so i18next is initialized

// ReactDOM.render(<App />, document.getElementById("root"));

function App() {
  const [participantName, setParticipantName] = useState("");
  const sequenceId = 7; // Set your sequenceId accordingly

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
