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
import Cookies from "js-cookie";
import { useTranslation } from "react-i18next";

function Questionnaire({ sequenceId, participantName }) {
    const { t } = useTranslation();

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
    const [currentAudioSrc, setCurrentAudioSrc] = useState("");
    const [timeUsed, setTimeUsed] = useState(0);

    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes.toString().padStart(2, "0")}:${secs
            .toString()
            .padStart(2, "0")}`;
    };

    // Load persisted state on component mount
    useEffect(() => {
        const savedTrialIndex = Cookies.get("currentTrialIndex");
        if (savedTrialIndex) {
            setCurrentTrialIndex(parseInt(savedTrialIndex, 10));
        }
    }, []);

    // Persist currentTrialIndex whenever it changes
    useEffect(() => {
        Cookies.set("currentTrialIndex", currentTrialIndex, { expires: 7 });
    }, [currentTrialIndex]);

    // Timer update
    useEffect(() => {
        const timerId = setInterval(() => {
            setTimeUsed((prev) => prev + 1);
        }, 1000);
        return () => clearInterval(timerId);
    }, []);

    // Fetch trials and audio info
    useEffect(() => {
        setLoading(true);
        fetch(`/api/trials/${sequenceId}`)
            .then((res) => res.json())
            .then((data) => {
                if (data.error) {
                    showSnackbar(data.error, "error");
                } else {
                    setTrials(data.trials);
                    const updatedAudioMap = Object.fromEntries(
                        Object.entries(data.audio_map).map(([key, path]) => [
                            key,
                            `path.replace(/\\/g, "/").trim()`,
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
            audioPlayer.audio.current.pause();
            setIsPlaying(false);
        } else {
            setCurrentAudioSrc(audioPath);
        }
    }

    useEffect(() => {
        if (audioPlayer && currentAudioSrc) {
            audioPlayer.audio.current.play();
            setIsPlaying(true);
        }
    }, [currentAudioSrc, audioPlayer]);

    // Reset playback state when moving to next trial
    useEffect(() => {
        setCurrentAudioSrc("");
        setIsPlaying(false);
    }, [currentTrialIndex]);

    function handleSkipTrial() {
        setLoading(true);
        fetch(`/api/trials/${sequenceId}/${currentTrialIndex}/submit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                participant_name: participantName,
                best_stimulus: null,
                worst_stimulus: null,
                resources_in_trial: trials[currentTrialIndex],
            }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.error) {
                    showSnackbar(t("questionnaire.errorSkipping"), "error");
                } else {
                    showSnackbar(t("questionnaire.trialSkipped"), "success");
                    setCurrentTrialIndex((i) => i + 1);
                }
            })
            .catch((err) => {
                showSnackbar(t("questionnaire.errorSkipping"), "error");
                console.error(err);
            })
            .finally(() => setLoading(false));
    }

    function handleSubmitTrial() {
        if (bestChoice == null || worstChoice == null) {
            showSnackbar(t("questionnaire.selectBoth"), "warning");
            return;
        }
        if (bestChoice === worstChoice) {
            showSnackbar(t("questionnaire.sameSelection"), "warning");
            return;
        }

        setLoading(true);
        fetch(`/api/trials/${sequenceId}/${currentTrialIndex}/submit`, {
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
                    showSnackbar(t("questionnaire.errorSubmitting"), "error");
                } else {
                    showSnackbar(t("questionnaire.trialSubmitted"), "success");
                    setBestChoice(null);
                    setWorstChoice(null);
                    setCurrentTrialIndex((i) => i + 1);
                }
            })
            .catch((err) => {
                showSnackbar(t("questionnaire.errorSubmitting"), "error");
                console.error(err);
            })
            .finally(() => setLoading(false));
    }

    function handleFinish() {
        setLoading(true);
        fetch(`/api/trials/${sequenceId}/finalize`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ participant_name: participantName }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.error) {
                    showSnackbar(data.error, "error");
                } else {
                    setFinalResults(data.sorted_stimuli);
                    showSnackbar(t("questionnaire.completeMessage"), "success");
                }
            })
            .catch((err) => {
                showSnackbar("Error finalizing results.", "error");
                console.error(err);
            })
            .finally(() => setLoading(false));
    }

    if (finalResults) {
        // Reset only the trial progress cookie and reload the page
        const handleRestart = () => {
            Cookies.remove("currentTrialIndex");
            window.location.reload();
        };

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
                        {t("questionnaire.thankYou")}
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 3 }}>
                        {t("questionnaire.resultsMessage")}
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
                        {t("questionnaire.restart")}
                    </Button>
                    {/* "Do Trial Again" box that resets only the trial cookie */}
                    <Box
                        sx={{
                            mt: 3,
                            border: "1px dashed grey",
                            p: 2,
                            borderRadius: 2,
                        }}
                    >
                        <Typography variant="subtitle1" gutterBottom>
                            {t("questionnaire.doTrialAgain")}
                        </Typography>
                        <Button
                            variant="outlined"
                            color="secondary"
                            onClick={handleRestart}
                        >
                            {t("questionnaire.resetAndRestart")}
                        </Button>
                    </Box>
                </Box>
            </Container>
        );
    }


    if (currentTrialIndex >= trials.length && trials.length > 0) {
        // Add a function to reset the cookie
        const handleRestart = () => {
            Cookies.remove("currentTrialIndex");
            window.location.reload();
        };

        return (
            <Container maxWidth="md" sx={{ mt: 5, textAlign: "center" }}>
                <Typography variant="h4" gutterBottom>
                    {t("questionnaire.completeMessage")}
                </Typography>
                <Typography variant="body1" sx={{ mb: 3 }}>
                    {t("questionnaire.participant", { participantName })}
                </Typography>

                {/* Finalize button */}
                <Button variant="contained" onClick={handleFinish}>
                    {t("questionnaire.finalizeResults")}
                </Button>

                {/* RESTART BUTTON (clears the trial cookie and restarts) */}
                <Box sx={{ mt: 2 }}>
                    <Button variant="outlined" color="secondary" onClick={handleRestart}>
                        {t("questionnaire.restart")}
                    </Button>
                </Box>

                <Snackbar
                    open={snackbar.open}
                    autoHideDuration={3000}
                    onClose={handleCloseSnackbar}
                >
                    <Alert
                        severity={snackbar.severity}
                        onClose={handleCloseSnackbar}
                        sx={{ width: "100%" }}
                    >
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
                    {t("questionnaire.loading")}
                </Typography>
            </Container>
        );
    }

    if (trials.length === 0) {
        return (
            <Container maxWidth="md" sx={{ mt: 5 }}>
                <Typography variant="h6">
                    {t("questionnaire.noTrials")}
                </Typography>
            </Container>
        );
    }

    const resourcesInCurrentTrial = trials[currentTrialIndex];
    const progressValue =
        ((currentTrialIndex + 1) / trials.length) * 100;

    return (
        <Container maxWidth="md" sx={{ mt: 5 }}>
            <Box
                sx={{
                    mb: 2,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >
                <Typography variant="body2">
                    {t("questionnaire.trialInfo", {
                        current: currentTrialIndex + 1,
                        total: trials.length,
                    })}
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
                    {t("questionnaire.participant", { participantName })}
                </Typography>
            </Box>

            {currentAudioSrc && (
                <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" sx={{ mb: 1 }}>
                        {t("questionnaire.nowPlaying")}
                    </Typography>
                    <ReactAudioPlayer
                        ref={(player) => setAudioPlayer(player)}
                        src={currentAudioSrc}
                        controls
                        onLoadedMetadata={(e) => {
                            e.target.play();
                            setIsPlaying(true);
                        }}
                        showJumpControls={false}
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
                                <TableCell sx={{ fontWeight: "bold" }}>
                                    {t("questionnaire.stimulus")}
                                </TableCell>
                                <TableCell sx={{ fontWeight: "bold" }}>
                                    {t("questionnaire.mostWarmth")}
                                </TableCell>
                                <TableCell sx={{ fontWeight: "bold" }}>
                                    {t("questionnaire.mostCold")}
                                </TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {resourcesInCurrentTrial.map((resId) => (
                                <TableRow key={resId}>
                                    <TableCell>
                                        <Button
                                            variant={
                                                audioMap[resId] === currentAudioSrc
                                                    ? "contained"
                                                    : "outlined"
                                            }
                                            color={
                                                audioMap[resId] === currentAudioSrc
                                                    ? "secondary"
                                                    : "primary"
                                            }
                                            onClick={() => handleLoadAudio(resId)}
                                            sx={{
                                                textTransform: "none",
                                                borderRadius: 0,
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
                    {t("questionnaire.submit")}
                </Button>
                <Button
                    variant="outlined"
                    color="secondary"
                    onClick={handleSkipTrial}
                    sx={{ textTransform: "none", borderRadius: 0, fontWeight: "bold", px: 3 }}
                >
                    {t("questionnaire.skip")}
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
