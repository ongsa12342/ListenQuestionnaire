// Questionnaire.jsx
import React, { useState, useEffect } from "react";
import {
    Container,
    Box,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Radio,
    FormControlLabel,
    RadioGroup,
    Button,
    CircularProgress,
    Snackbar,
    Alert,
    LinearProgress,
    Fade,
} from "@mui/material";
import ReactAudioPlayer from "react-h5-audio-player";
import "react-h5-audio-player/src/styles.scss";
import CheckIcon from "@mui/icons-material/Check";

function Questionnaire({ sequenceId, participantName }) {
    const [trials, setTrials] = useState([]);
    const [audioMap, setAudioMap] = useState({});
    const [currentTrialIndex, setCurrentTrialIndex] = useState(0);
    const [bestChoice, setBestChoice] = useState(null);
    const [worstChoice, setWorstChoice] = useState(null);
    const [loading, setLoading] = useState(false);
    const [snackbar, setSnackbar] = useState({
        open: false,
        message: "",
        severity: "info",
    });
    const [finalResults, setFinalResults] = useState(null);

    // Which audio is currently loaded in the player
    const [currentAudioSrc, setCurrentAudioSrc] = useState("");

    const [timeUsed, setTimeUsed] = useState(0);

    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };


    // Update the useEffect for the timer:
    useEffect(() => {
        const timerId = setInterval(() => {
            setTimeUsed((prev) => prev + 1);
        }, 1000);
        return () => clearInterval(timerId);
    }, []);

    useEffect(() => {
        setLoading(true);
        fetch(`/api/trials / ${sequenceId}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.error) {
                    showSnackbar(data.error, "error");
                } else {
                    setTrials(data.trials); // e.g. [[resId1, resId2], ...]
                    // Prepend STATIC_URL to each audio file path if needed
                    const updatedAudioMap = Object.fromEntries(
                        Object.entries(data.audio_map).map(([key, path]) => [
                            key,
                            `/ ${path.replace(/\\/g, "/")}`,
                        ])
                    );
                    setAudioMap(updatedAudioMap);
                }
            })
            .catch((err) => {
                showSnackbar("Error loading trials.", "error");
                console.error(err);
            })
            .finally(() => setLoading(false));
    }, [sequenceId]);

    function showSnackbar(message, severity = "info") {
        setSnackbar({ open: true, message, severity });
    }

    function handleCloseSnackbar() {
        setSnackbar((prev) => ({ ...prev, open: false }));
    }

    const [audioPlayer, setAudioPlayer] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);


    function handleLoadAudio(resourceId) {
        const audioPath = audioMap[resourceId];
        if (!audioPath) return;

        if (currentAudioSrc === audioPath && isPlaying) {
            // Stop if the same audio is playing
            audioPlayer.audio.current.pause();
            setIsPlaying(false);
        } else {
            // Play new audio
            setCurrentAudioSrc(audioPath);
            setTimeout(() => {
                if (audioPlayer) {
                    audioPlayer.audio.current.play();
                    setIsPlaying(true);
                }
            }, 100);
        }
    }

    // Reset playback state when moving to next trial
    useEffect(() => {
        setCurrentAudioSrc("");
        setIsPlaying(false);
    }, [currentTrialIndex]);

    function handleSkipTrial() {
        setLoading(true);
        // Instead of relying on radio selections, we explicitly mark this trial as skipped
        fetch(`/ api / trials / ${sequenceId} / ${currentTrialIndex} / submit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                participant_name: participantName,
                best_stimulus: null,  // using -1 to denote skipped
                worst_stimulus: null, // using -1 to denote skipped
                resources_in_trial: trials[currentTrialIndex],
            }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.error) {
                    showSnackbar(data.error, "error");
                } else {
                    showSnackbar("Trial skipped successfully!", "success");
                    // Move on to next trial
                    setCurrentTrialIndex((i) => i + 1);
                }
            })
            .catch((err) => {
                showSnackbar("Error skipping trial.", "error");
                console.error(err);
            })
            .finally(() => setLoading(false));
    }


    function handleSubmitTrial() {
        if (bestChoice == null || worstChoice == null) {
            showSnackbar("Please select both Best and Worst.", "warning");
            return;
        }
        if (bestChoice === worstChoice) {
            showSnackbar("Best and Worst cannot be the same!", "warning");
            return;
        }

        setLoading(true);
        fetch(`/ api / trials / ${sequenceId} / ${currentTrialIndex} / submit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                participant_name: participantName,
                best_stimulus: bestChoice,
                worst_stimulus: worstChoice,
                resources_in_trial: trials[currentTrialIndex],
            }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.error) {
                    showSnackbar(data.error, "error");
                } else {
                    showSnackbar("Trial submitted successfully!", "success");
                    setBestChoice(null);
                    setWorstChoice(null);
                    setCurrentTrialIndex((i) => i + 1);
                }
            })
            .catch((err) => {
                showSnackbar("Error submitting trial.", "error");
                console.error(err);
            })
            .finally(() => setLoading(false));
    }

    function handleFinish() {
        setLoading(true);
        fetch(`/ api / trials / ${sequenceId} / finalize`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ participant_name: participantName }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.error) {
                    showSnackbar(data.error, "error");
                } else {
                    setFinalResults(data.sorted_stimuli); // Save the final results
                    showSnackbar("All trials completed!", "success");
                }
            })
            .catch((err) => {
                showSnackbar("Error finalizing results.", "error");
                console.error(err);
            })
            .finally(() => setLoading(false));
    }

    if (finalResults) {
        return (
            <Container maxWidth="md" sx={{ mt: 5, textAlign: "center" }}>
                <Box
                    sx={{
                        backgroundColor: "white",
                        borderRadius: 3,
                        boxShadow: 3,
                        p: 4,
                        textAlign: "center",
                    }}
                >
                    <CheckIcon sx={{ fontSize: 60, color: "green", mb: 2 }} />
                    <Typography variant="h4" gutterBottom>
                        Thank You for Participating!
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 3 }}>
                        Here are the final rankings of the stimuli based on your selections:
                    </Typography>
                    <Fade in={true} timeout={600}>
                        <Box
                            sx={{
                                display: "flex",
                                flexDirection: "column",
                                alignItems: "center",
                            }}
                        >
                            {finalResults.map((stimulus, index) => (
                                <Box
                                    key={index}
                                    sx={{
                                        width: "100%",
                                        maxWidth: 400,
                                        p: 2,
                                        my: 1,
                                        backgroundColor: index === 0 ? "primary.main" : "grey.100",
                                        color: index === 0 ? "white" : "black",
                                        borderRadius: 2,
                                        boxShadow: 1,
                                        fontWeight: index === 0 ? "bold" : "normal",
                                        textAlign: "center",
                                    }}
                                >
                                    {index + 1}. {stimulus.filename} - Score: {stimulus.score} - {stimulus.resource_id}
                                </Box>
                            ))}

                        </Box>
                    </Fade>
                    <Button
                        variant="contained"
                        color="primary"
                        sx={{ mt: 3, px: 4, borderRadius: 2 }}
                        onClick={() => window.location.reload()}
                    >
                        Restart
                    </Button>
                </Box>
            </Container>
        );
    }


    if (currentTrialIndex >= trials.length && trials.length > 0) {
        return (
            <Container maxWidth="md" sx={{ mt: 5 }}>
                <Typography variant="h4" gutterBottom>
                    All Trials Completed!
                </Typography>
                <Typography variant="body1" sx={{ mb: 3 }}>
                    Thank you for participating, {participantName}.
                </Typography>
                <Button variant="contained" onClick={handleFinish}>
                    Finalize and See Results
                </Button>
                <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={handleCloseSnackbar}>
                    <Alert severity={snackbar.severity} onClose={handleCloseSnackbar} sx={{ width: "100%" }}>
                        {snackbar.message}
                    </Alert>
                </Snackbar>
            </Container>
        );
    }

    if (loading) {
        return (
            <Container maxWidth="md" sx={{ mt: 5, textAlign: "center" }}>
                <CircularProgress />
                <Typography variant="body1" sx={{ mt: 2 }}>
                    Loading...
                </Typography>
            </Container>
        );
    }

    if (trials.length === 0) {
        return (
            <Container maxWidth="md" sx={{ mt: 5 }}>
                <Typography variant="h6">No trials available.</Typography>
            </Container>
        );
    }

    const resourcesInCurrentTrial = trials[currentTrialIndex];
    const progressValue = ((currentTrialIndex + 1) / trials.length) * 100;

    return (
        <Container maxWidth="md" sx={{ mt: 5 }}>
            {/* Progress and Timer in the same row */}
            <Box
                sx={{
                    mb: 2,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >
                <Typography variant="body2">
                    Trial {currentTrialIndex + 1} of {trials.length}
                </Typography>
                <Typography variant="body2" color="primary">
                    {formatTime(timeUsed)}
                </Typography>
            </Box>
            <LinearProgress variant="determinate" value={progressValue} />

            <Box sx={{ textAlign: "center", mb: 4, mt: 3 }}>
                <Typography variant="h4" gutterBottom>
                    Questionnaire
                </Typography>
                <Typography variant="subtitle1" sx={{ mb: 2 }}>
                    Participant: {participantName}
                </Typography>
            </Box>

            {currentAudioSrc && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" sx={{ mb: 1 }}>
                        Now Playing:
                    </Typography>
                    <ReactAudioPlayer
                        ref={(player) => setAudioPlayer(player)}
                        src={currentAudioSrc}
                        controls
                        showJumpControls={false} // Remove skip buttons
                        showDownloadProgress={false}
                        showFilledProgress={false}
                        style={{ width: "100%" }}
                    />

                </Box>
            )}



            <Fade in={true} timeout={600}>
                <TableContainer component={Paper} sx={{ mb: 3 }}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell sx={{ fontWeight: "bold" }}>Stimulus</TableCell>
                                <TableCell sx={{ fontWeight: "bold" }}>Best</TableCell>
                                <TableCell sx={{ fontWeight: "bold" }}>Worst</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {resourcesInCurrentTrial.map((resId) => (
                                <TableRow key={resId}>
                                    <TableCell>
                                        <Button
                                            variant={audioMap[resId] === currentAudioSrc ? "contained" : "outlined"}
                                            color={audioMap[resId] === currentAudioSrc ? "secondary" : "primary"}
                                            onClick={() => handleLoadAudio(resId)}
                                            sx={{
                                                textTransform: "none",
                                                borderRadius: 0, // Square button style (minimal design)
                                                fontWeight: "bold",
                                            }}
                                        >
                                            {audioMap[resId] === currentAudioSrc ? "Playing" : "Play"}
                                        </Button>
                                    </TableCell>
                                    <TableCell>
                                        <RadioGroup>
                                            <FormControlLabel
                                                control={
                                                    <Radio
                                                        checked={bestChoice === resId}
                                                        onChange={() => setBestChoice(resId)}
                                                    />
                                                }
                                                label=""
                                            />
                                        </RadioGroup>
                                    </TableCell>
                                    <TableCell>
                                        <RadioGroup>
                                            <FormControlLabel
                                                control={
                                                    <Radio
                                                        checked={worstChoice === resId}
                                                        onChange={() => setWorstChoice(resId)}
                                                    />
                                                }
                                                label=""
                                            />
                                        </RadioGroup>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Fade>

            <Box sx={{ display: "flex", justifyContent: "center", mb: 5 }}>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={handleSubmitTrial}
                    sx={{ mr: 2, textTransform: "none", borderRadius: 0, fontWeight: "bold", px: 3 }}
                >
                    Submit
                </Button>
                <Button
                    variant="outlined"
                    color="secondary"
                    onClick={handleSkipTrial}
                    sx={{ textTransform: "none", borderRadius: 0, fontWeight: "bold", px: 3 }}
                >
                    Skip
                </Button>
            </Box>

            <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={handleCloseSnackbar}>
                <Alert severity={snackbar.severity} onClose={handleCloseSnackbar} sx={{ width: "100%" }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Container>
    );
}

export default Questionnaire;
