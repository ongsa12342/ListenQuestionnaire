import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";
import Questionnaire from "./Questionnaire";
import SimilarityQuestionnaire from "./SimilarityQuestionnaire";
import LandingPage from "./LandingPage";
import NewLandingPage from "./NewLandingPage";
import "./i18n";
import Cookies from "js-cookie";

const theme = createTheme({
  palette: {
    primary: {
      main: "#1976d2",
    },
    secondary: {
      main: "#9c27b0",
    },
  },
  typography: {
    fontFamily: "'Roboto', sans-serif",
  },
});

function App() {
  const [participantName, setParticipantName] = useState("");
  const sequenceIdEx1 = 7;
  const sequenceIdEx2 = 8;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/ex1" />} />
          <Route
            path="/ex1"
            element={
              participantName ? (
                <Questionnaire
                  sequenceId={sequenceIdEx1}
                  participantName={participantName}
                />
              ) : (
                <LandingPage onStart={(name) => setParticipantName(name)} />
              )
            }
          />
          <Route path="/ex2" element={<NewLandingPage />} />
          <Route
            path="/ex2/questionnaire"
            element={
              <SimilarityQuestionnaire
                sequenceId={sequenceIdEx2}
                participantName={Cookies.get("participantName") || ""}
              />
            }
          />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
