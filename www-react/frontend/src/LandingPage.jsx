// LandingPage.jsx
import React, { useState } from "react";
import {
    Container,
    Box,
    Typography,
    TextField,
    Button,
    Checkbox,
    FormControlLabel,
    FormHelperText,
    Stack,
} from "@mui/material";

function LandingPage({ onStart }) {
    const [name, setName] = useState("");
    const [error, setError] = useState(false);
    const [agreed, setAgreed] = useState(false);
    const [agreeError, setAgreeError] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (name.trim() === "") {
            setError(true);
            return;
        }
        if (!agreed) {
            setAgreeError(true);
            return;
        }
        setError(false);
        setAgreeError(false);
        onStart(name);
    };

    return (
        <Container maxWidth="sm" sx={{ mt: 5 }}>
            {/* Outer Box for the heading and intro text */}
            <Box
                sx={{
                    textAlign: "left",
                    mb: 4,
                    p: 3,
                    border: "1px solid #ccc",
                    borderRadius: 2,
                }}
            >
                <Typography variant="h4" gutterBottom>
                    Welcome to the Questionnaire
                </Typography>

                {/* First paragraph */}
                <Typography variant="body1" sx={{ mb: 2 }}>
                    This questionnaire is designed to gather your opinions on various audio stimuli
                    as part of a research study. In each trial, you will listen to a set of audio clips
                    and select the option you think is the best and the one you think is the worst.
                    Your feedback will help us understand preferences and make informed improvements.
                </Typography>

                {/* Subtitle for "What to Do" */}
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                    What to Do:
                </Typography>

                {/* Use a list for steps */}
                <ul style={{ margin: 0, paddingLeft: '1.25rem', marginBottom: '1rem' }}>
                    <li><strong>Listen:</strong> Play the audio clips provided in each trial.</li>
                    <li><strong>Select:</strong> Choose the best and worst stimuli for each trial.</li>
                    <li><strong>Submit:</strong> Confirm your choices and move on to the next trial.</li>
                </ul>

                {/* Another paragraph for final details */}
                <Typography variant="body1" sx={{ mb: 2 }}>
                    This study is being conducted as part of my senior project at FIBO KMUTT and is strictly for research purposes.
                </Typography>

                {/* Form is left-aligned, but still inside the same box */}
                <form onSubmit={handleSubmit} style={{ textAlign: "left" }}>
                    <Stack spacing={1}>
                        <TextField
                            label="Your Name"
                            variant="outlined"
                            fullWidth
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            error={error}
                            helperText={error ? "Please enter your name to continue." : ""}
                        />

                        {/* Checkbox and its error message */}
                        <Box>
                            <FormControlLabel
                                control={
                                    <Checkbox
                                        checked={agreed}
                                        onChange={(e) => {
                                            setAgreed(e.target.checked);
                                            if (e.target.checked) setAgreeError(false);
                                        }}
                                        name="consent"
                                        color="primary"
                                        sx={{ transform: "scale(0.8)" }} // Slightly smaller checkbox
                                    />
                                }
                                label={
                                    <span style={{ fontSize: "0.9rem" }}>
                                        I consent to the collection and use of my data for research purposes.
                                    </span>
                                }
                            />
                            {agreeError && (
                                <FormHelperText error sx={{ ml: 2, mt: 0 }}>
                                    Please agree to proceed.
                                </FormHelperText>
                            )}
                        </Box>

                        {/* Submit Button */}
                        <Button type="submit" variant="contained" color="primary">
                            Start Questionnaire
                        </Button>
                    </Stack>
                </form>
            </Box>
        </Container>
    );
}

export default LandingPage;
