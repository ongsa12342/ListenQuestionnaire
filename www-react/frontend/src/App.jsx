// App.jsx
import React, { useState } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";
import LandingPage from "./LandingPage.jsx";
import Questionnaire from "./Questionnaire";

const theme = createTheme({
    palette: {
        primary: {
            main: "#1976d2", // Customize as you like
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
    const sequenceId = 5; // Set your sequenceId accordingly

    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            {participantName === "" ? (
                <LandingPage onStart={(name) => setParticipantName(name)} />
            ) : (
                <Questionnaire sequenceId={sequenceId} participantName={participantName} />
            )}
        </ThemeProvider>
    );
}

export default App;
