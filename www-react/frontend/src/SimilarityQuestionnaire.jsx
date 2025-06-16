import React, { useState, useEffect } from "react";
import {
    Container,
    Box,
    Typography,
    Paper,
    Button,
    CircularProgress,
    Snackbar,
    Alert,
    LinearProgress,
    Fade,
    Slider,
    Grid,
    Card,
    CardContent,
    Stack,
    IconButton,
} from "@mui/material";
import ReactAudioPlayer from "react-h5-audio-player";
import "react-h5-audio-player/src/styles.scss";
import CheckIcon from "@mui/icons-material/Check";
import Cookies from "js-cookie";
import { useTranslation } from "react-i18next";
import { styled } from "@mui/material/styles";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import PauseIcon from "@mui/icons-material/Pause";

// Custom styled vertical slider
const VerticalSlider = styled(Slider)(({ theme }) => ({
    height: 300,
    '& .MuiSlider-markLabel': {
        transform: 'translateX(30px)',
        fontSize: '0.875rem',
        fontWeight: 500,
    },
    '& .MuiSlider-mark': {
        width: 8,
        height: 1,
        backgroundColor: theme.palette.grey[400],
    },
    '& .MuiSlider-track': {
        backgroundColor: theme.palette.primary.main,
    },
    '& .MuiSlider-rail': {
        backgroundColor: theme.palette.grey[300],
    },
}));

// Styled audio player container
const AudioPlayerContainer = styled(Box)(({ theme }) => ({
    '& .rhap_container': {
        backgroundColor: theme.palette.background.paper,
        boxShadow: theme.shadows[1],
        width: '100%',
        maxWidth: 400,
    },
    '& .rhap_main-controls-button': {
        color: theme.palette.primary.main,
    },
    '& .rhap_progress-filled': {
        backgroundColor: theme.palette.primary.main,
    },
    '& .rhap_download-progress': {
        backgroundColor: theme.palette.grey[200],
    },
}));

function SimilarityQuestionnaire({ sequenceId, participantName }) {
    const { t } = useTranslation();

    // Predefined audio pairs
    const audioPairs = [
        {
            id: "VOXac30",
            reference: {
                id: 1069,
                filename: "VOXac30_Reference.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_VOXac30_custom.wav"
            },
            predicted: {
                id: 1070,
                filename: "VOXac30_Simulated.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_VOXac30_custom_predicted.wav"
            }
        },
        {
            id: "RolandJazzChorus",
            reference: {
                id: 1067,
                filename: "RolandJazzChorus_Reference.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Roland_Jazz_Chorus.wav"
            },
            predicted: {
                id: 1068,
                filename: "RolandJazzChorus_Simulated.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Roland_Jazz_Chorus_predicted.wav"
            }
        },
        {
            id: "OrangeRocker30Head",
            reference: {
                id: 1065,
                filename: "OrangeRocker30Head_Reference.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Orange_Rocker30_Head.wav"
            },
            predicted: {
                id: 1066,
                filename: "OrangeRocker30Head_Simulated.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Orange_Rocker30_Head_predicted.wav"
            }
        },
        {
            id: "MarshallJCM800",
            reference: {
                id: 1063,
                filename: "MarshallJCM800_Reference.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Marshall_JCM800.wav"
            },
            predicted: {
                id: 1064,
                filename: "MarshallJCM800_Simulated.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Marshall_JCM800_predicted.wav"
            }
        },
        {
            id: "Marshall1959Plexi",
            reference: {
                id: 1061,
                filename: "Marshall1959Plexi_Reference.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Marshall_1959Plexi.wav"
            },
            predicted: {
                id: 1062,
                filename: "Marshall1959Plexi_Simulated.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Marshall_1959Plexi_predicted.wav"
            }
        },
        {
            id: "Fenderdeluxereverb",
            reference: {
                id: 1059,
                filename: "Fenderdeluxereverb_Reference.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Fender_deluxe_reverb.wav"
            },
            predicted: {
                id: 1060,
                filename: "Fenderdeluxereverb_Simulated.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Fender_deluxe_reverb_predicted.wav"
            }
        },
        {
            id: "FenderBassman50Head",
            reference: {
                id: 1057,
                filename: "FenderBassman50Head_Reference.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Fender_Bassman50_Head.wav"
            },
            predicted: {
                id: 1058,
                filename: "FenderBassman50Head_Simulated.wav",
                url: "https://dataset-guitar.s3.ap-southeast-1.amazonaws.com/Example/Pop_Fender_Bassman50_Head_predicted.wav"
            }
        }
    ];

    const [trials, setTrials] = useState([]);
    const [audioMap, setAudioMap] = useState({});
    const [currentTrialIndex, setCurrentTrialIndex] = useState(0);
    const [ratings, setRatings] = useState({});
    const [loading, setLoading] = useState(false);
    const [snackbar, setSnackbar] = useState({
        open: false,
        message: "",
        severity: "info",
    });
    const [finalResults, setFinalResults] = useState(null);
    const [currentAudioSrc, setCurrentAudioSrc] = useState("");
    const [timeUsed, setTimeUsed] = useState(0);
    const [playingResourceId, setPlayingResourceId] = useState(null);

    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    // Load persisted state on component mount
    useEffect(() => {
        const savedTrialIndex = Cookies.get("similarityTrialIndex");
        if (savedTrialIndex) {
            setCurrentTrialIndex(parseInt(savedTrialIndex, 10));
        }
    }, []);

    // Persist currentTrialIndex whenever it changes
    useEffect(() => {
        Cookies.set("similarityTrialIndex", currentTrialIndex, { expires: 7 });
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
                            path.replace(/\\/g, "/").trim(),
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

    function handlePlayPause(resourceId) {
        const audioPath =
            resourceId === "reference"
                ? audioMap[trials[currentTrialIndex]?.[0]] // First item in trial is reference
                : audioMap[resourceId];

        if (!audioPath) {
            console.warn("No audio path found for:", resourceId);
            return;
        }

        // If clicking the same button (same resourceId)
        if (playingResourceId === resourceId) {
            if (isPlaying) {
                // Pause the current audio
                audioPlayer?.audio?.current?.pause();
                setIsPlaying(false);
            } else {
                // Resume the current audio
                audioPlayer?.audio?.current?.play()
                    .then(() => setIsPlaying(true))
                    .catch(error => console.error('Resume failed:', error));
            }
            return;
        }

        // If clicking a different button
        // Stop current playback, reset, and play new audio from beginning
        if (audioPlayer?.audio?.current) {
            audioPlayer.audio.current.pause();
            audioPlayer.audio.current.currentTime = 0;
        }

        setIsPlaying(false);
        setPlayingResourceId(resourceId);
        setCurrentAudioSrc(""); // Clear current source

        // Set new source and play after a brief delay
        setTimeout(() => {
            setCurrentAudioSrc(audioPath);
        }, 50);
    }

    // Add logging to audio player events
    useEffect(() => {
        if (audioPlayer && currentAudioSrc) {
            console.log('Audio player ready, attempting to play:', currentAudioSrc);
            audioPlayer.audio.current.play()
                .then(() => {
                    console.log('Playback started successfully');
                    setIsPlaying(true);
                })
                .catch(error => console.error('Playback failed:', error));
        }
    }, [currentAudioSrc, audioPlayer]);

    // Reset playback state when moving to next trial
    useEffect(() => {
        setCurrentAudioSrc("");
        setIsPlaying(false);
        setPlayingResourceId(null);

        if (trials.length > 0 && currentTrialIndex < trials.length) {
            const initialRatings = {};
            trials[currentTrialIndex]?.slice(1).forEach(resId => {
                initialRatings[resId] = 100;
            });
            setRatings(initialRatings);
        } else {
            setRatings({});
        }
    }, [currentTrialIndex, trials]);

    function handleRatingChange(resourceId, value) {
        setRatings((prev) => ({
            ...prev,
            [resourceId]: value,
        }));
    }

    function handleSubmitTrial() {
        const currentTrialResources = trials[currentTrialIndex] || [];
        const allRated = currentTrialResources
            .slice(1)
            .every((resId) => typeof ratings[resId] === "number");

        if (!allRated) {
            showSnackbar(
                t("similarityQuestionnaire.rateAll"),
                "warning"
            );
            return;
        }

        setLoading(true);
        fetch(`/api/trials/${sequenceId}/${currentTrialIndex}/submit_similar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                participant_name: participantName,
                ratings: ratings,
                resources_in_trial: trials[currentTrialIndex],
            }),
        })
            .then((res) => res.json())
            .then((data) => {
                if (data.error) {
                    showSnackbar(t("similarityQuestionnaire.errorSubmitting"), "error");
                } else {
                    showSnackbar(t("similarityQuestionnaire.trialSubmitted"), "success");
                    setCurrentTrialIndex((i) => i + 1);
                }
            })
            .catch((err) => {
                showSnackbar(t("similarityQuestionnaire.errorSubmitting"), "error");
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
                    showSnackbar(t("similarityQuestionnaire.completeMessage"), "success");
                }
            })
            .catch((err) => {
                showSnackbar("Error finalizing results.", "error");
                console.error(err);
            })
            .finally(() => setLoading(false));
    }

    if (finalResults) {
        const handleRestart = () => {
            Cookies.remove("similarityTrialIndex");
            window.location.reload();
        };

        return (
            <Container maxWidth="md" sx={{ mt: 5, textAlign: "center" }}>
                <Box sx={{ backgroundColor: "white", borderRadius: 3, boxShadow: 3, p: 4 }}>
                    <CheckIcon sx={{ fontSize: 60, color: "green", mb: 2 }} />
                    <Typography variant="h4" gutterBottom>
                        {t("similarityQuestionnaire.thankYou")}
                    </Typography>
                    <Typography variant="body1" sx={{ mb: 3 }}>
                        {t("similarityQuestionnaire.resultsMessage")}
                    </Typography>
                    <Fade in={true} timeout={600}>
                        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
                            {audioPairs.map((pair) => (
                                <Paper
                                    key={pair.id}
                                    elevation={2}
                                    sx={{
                                        p: 3,
                                        backgroundColor: 'background.paper',
                                        borderRadius: 2
                                    }}
                                >
                                    <Typography variant="h5" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
                                        {pair.id}
                                    </Typography>
                                    <Grid container spacing={2}>
                                        <Grid item xs={6}>
                                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                Reference Sound
                                            </Typography>
                                            <Box sx={{
                                                p: 2,
                                                backgroundColor: 'grey.100',
                                                borderRadius: 1,
                                                mb: 1
                                            }}>
                                                <Typography variant="body2">
                                                    {pair.reference.filename}
                                                </Typography>
                                            </Box>
                                            <ReactAudioPlayer
                                                key={`ref-${pair.id}}`}
                                                src={pair.reference.url}
                                                controls
                                                style={{ width: '100%' }}
                                                autoPlayAfterSrcChange={false}
                                                onPlay={() => {
                                                    const audio = document.querySelector(`audio[src="${pair.reference.url}"]`);
                                                    if (audio) {
                                                        audio.currentTime = 0;
                                                    }
                                                }}
                                            />
                                        </Grid>
                                        <Grid item xs={6}>
                                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                Predicted Sound
                                            </Typography>
                                            <Box sx={{
                                                p: 2,
                                                backgroundColor: 'grey.100',
                                                borderRadius: 1,
                                                mb: 1
                                            }}>
                                                <Typography variant="body2">
                                                    {pair.predicted.filename}
                                                </Typography>
                                            </Box>
                                            <ReactAudioPlayer
                                                key={`pred-${pair.id}}`}
                                                src={pair.predicted.url}
                                                controls
                                                style={{ width: '100%' }}
                                                autoPlayAfterSrcChange={false}
                                                onPlay={() => {
                                                    const audio = document.querySelector(`audio[src="${pair.predicted.url}"]`);
                                                    if (audio) {
                                                        audio.currentTime = 0;
                                                    }
                                                }}
                                            />
                                        </Grid>
                                    </Grid>
                                </Paper>
                            ))}
                        </Box>
                    </Fade>
                    <Button
                        variant="contained"
                        color="primary"
                        sx={{ mt: 3 }}
                        onClick={handleRestart}
                    >
                        {t("similarityQuestionnaire.restart")}
                    </Button>
                </Box>
            </Container>
        );
    }

    if (currentTrialIndex >= trials.length && trials.length > 0) {
        return (
            <Container maxWidth="md" sx={{ mt: 5, textAlign: "center" }}>
                <Typography variant="h4" gutterBottom>
                    {t("similarityQuestionnaire.completeMessage")}
                </Typography>
                <Typography variant="body1" sx={{ mb: 3 }}>
                    {t("similarityQuestionnaire.participant", { participantName })}
                </Typography>
                <Button variant="contained" onClick={handleFinish}>
                    {t("similarityQuestionnaire.finalizeResults")}
                </Button>
            </Container>
        );
    }

    if (loading) {
        return (
            <Container maxWidth="md" sx={{ mt: 5, textAlign: "center" }}>
                <CircularProgress />
                <Typography variant="body1" sx={{ mt: 2 }}>
                    {t("similarityQuestionnaire.loading")}
                </Typography>
            </Container>
        );
    }

    if (trials.length === 0) {
        return (
            <Container maxWidth="md" sx={{ mt: 5 }}>
                <Typography variant="h6">
                    {t("similarityQuestionnaire.noTrials")}
                </Typography>
            </Container>
        );
    }

    const resourcesInCurrentTrial = trials[currentTrialIndex];

    return (
        <>
            <Box sx={{ height: '4px', background: 'linear-gradient(to right, #2196f3, #90caf9)', width: '100%' }} />
            <Container maxWidth="lg" sx={{ mt: 5, mb: 5 }}>
                {/* Progress and Timer */}
                <Box sx={{ mb: 2, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Typography variant="body2">
                        {t("similarityQuestionnaire.trialInfo", {
                            current: currentTrialIndex + 1,
                            total: trials.length,
                        })}
                    </Typography>
                    <Typography variant="body2" color="primary">
                        {formatTime(timeUsed)}
                    </Typography>
                </Box>
                <LinearProgress variant="determinate" value={(currentTrialIndex / trials.length) * 100} sx={{ mb: 4 }} />

                {/* Title and Instructions */}
                <Box sx={{ textAlign: "center", mb: 4 }}>
                    <Typography variant="h4" gutterBottom>
                        {t("similarityQuestionnaire.title")}
                    </Typography>
                    <Typography variant="subtitle1" gutterBottom>
                        {t("similarityQuestionnaire.participant", { participantName })}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        {t("similarityQuestionnaire.description")}
                    </Typography>
                </Box>

                {/* Reference Section */}
                <Box
                    sx={{
                        mb: 4,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                    }}
                >
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={() => handlePlayPause("reference")}
                        startIcon={
                            playingResourceId === "reference" && isPlaying ? (
                                <PauseIcon />
                            ) : (
                                <PlayArrowIcon />
                            )
                        }
                        sx={{
                            minWidth: 200,
                            mb: 2,
                            bgcolor: "#0277bd",
                            "&:hover": { bgcolor: "#0288d1" },
                        }}
                    >
                        {playingResourceId === "reference" && isPlaying
                            ? t("similarityQuestionnaire.pause")
                            : t("similarityQuestionnaire.reference")}
                    </Button>

                    {currentAudioSrc && (
                        <Box sx={{ width: "100%", maxWidth: 800 }}>
                            <ReactAudioPlayer
                                ref={(player) => setAudioPlayer(player)}
                                src={currentAudioSrc}
                                onEnded={() => setIsPlaying(false)}
                                onPause={() => setIsPlaying(false)}
                                onPlay={() => setIsPlaying(true)}
                                controls
                                style={{ width: '100%' }}
                                showJumpControls={false}
                                showDownloadProgress={false}
                                customControlsSection={[]}
                            />
                        </Box>
                    )}
                </Box>

                <RatingChart
                    ratings={ratings}
                    resourcesInCurrentTrial={resourcesInCurrentTrial}
                    playingResourceId={playingResourceId}
                    isPlaying={isPlaying}
                    handlePlayPause={handlePlayPause}
                    handleRatingChange={handleRatingChange}
                />

                {/* Action Buttons */}
                <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={handleSubmitTrial}
                        sx={{ mr: 2 }}
                        size="large"
                    >
                        {t("similarityQuestionnaire.submit")}
                    </Button>
                </Box>

                {/* Snackbar for notifications */}
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
        </>
    );
}

function RatingChart({
    ratings,
    resourcesInCurrentTrial,
    playingResourceId,
    isPlaying,
    handlePlayPause,
    handleRatingChange
}) {
    const { t } = useTranslation();
    const yAxisLineValues = [100, 80, 60, 40, 20, 0];
    const yAxisCategoryLabels = [
        t("similarityQuestionnaire.excellent"),
        t("similarityQuestionnaire.good"),
        t("similarityQuestionnaire.fair"),
        t("similarityQuestionnaire.poor"),
        t("similarityQuestionnaire.bad")
    ];
    const yAxisWidth = 120; // 40px for numbers, 80px for categories
    const chartGap = 16; // gap between y-axis and chart

    return (
        <Box sx={{ mt: 4, mb: 2 }}>
            {/* Row 1: Titles and Play Buttons */}
            <Box sx={{ display: 'flex', pl: `${yAxisWidth + chartGap}px` }}>
                <Box sx={{ flex: 1, display: 'flex', justifyContent: 'space-around' }}>
                    {resourcesInCurrentTrial?.slice(1).map((resId, index) => (
                        <Box
                            key={resId}
                            sx={{
                                width: 120,
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: 1,
                            }}
                        >
                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                {t("similarityQuestionnaire.condition")} {index + 1}
                            </Typography>
                            <Button
                                variant="outlined"
                                color="primary"
                                onClick={() => handlePlayPause(resId)}
                                startIcon={playingResourceId === resId && isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
                                sx={{ minWidth: 100 }}
                            >
                                {playingResourceId === resId && isPlaying ? t("similarityQuestionnaire.pause") : t("similarityQuestionnaire.play")}
                            </Button>
                        </Box>
                    ))}
                </Box>
            </Box>

            {/* Row 2: Y-Axis and Sliders */}
            <Box sx={{ display: 'flex', mt: 2 }}>
                {/* Y-AXIS */}
                <Box sx={{ width: yAxisWidth, mr: `${chartGap}px`, height: 300, display: 'flex' }}>
                    <Box sx={{ width: 40, height: '100%', position: "relative" }}>
                        {yAxisLineValues.map((value) => (
                            <Typography
                                key={value}
                                variant="body2"
                                sx={{
                                    position: "absolute",
                                    top: `${100 - value}%`,
                                    transform: "translateY(-50%)",
                                    textAlign: "right",
                                    width: "100%",
                                    fontWeight: 'bold'
                                }}
                            >
                                {value}
                            </Typography>
                        ))}
                    </Box>
                    <Box sx={{ width: 80, height: '100%', position: "relative" }}>
                        {yAxisCategoryLabels.map((label, index) => (
                            <Typography
                                key={label}
                                variant="body2"
                                sx={{
                                    position: "absolute",
                                    top: `${(index * 20) + 10}%`, // Position between lines
                                    transform: "translateY(-50%)",
                                    textAlign: "left",
                                    width: "100%",
                                    pl: 1,
                                    color: 'text.secondary'
                                }}
                            >
                                {label}
                            </Typography>
                        ))}
                    </Box>
                </Box>

                {/* Sliders and Grid Area */}
                <Box sx={{ flex: 1, position: "relative", height: 300 }}>
                    {/* Grid Lines */}
                    <Box sx={{ position: "absolute", top: 0, bottom: 0, left: 0, right: 0 }}>
                        {yAxisLineValues.map((value) => (
                            <Box
                                key={value}
                                sx={{
                                    position: "absolute",
                                    top: `${100 - value}%`,
                                    width: "100%",
                                    borderTop: "1px solid #e0e0e0",
                                }}
                            />
                        ))}
                    </Box>

                    {/* Sliders */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-around', height: '100%' }}>
                        {resourcesInCurrentTrial?.slice(1).map((resId) => (
                            <Box key={resId} sx={{ width: 120, display: 'flex', justifyContent: 'center' }}>
                                <VerticalSlider
                                    orientation="vertical"
                                    value={ratings[resId] ?? 100}
                                    onChange={(_, value) => handleRatingChange(resId, value)}
                                    marks={false}
                                    min={0}
                                    max={100}
                                    track="inverted"
                                    sx={{
                                        height: '100%',
                                        padding: 0,
                                        width: 36,
                                        '& .MuiSlider-thumb': {
                                            width: 36,
                                            height: 10,
                                            borderRadius: '3px',
                                            backgroundColor: '#fff',
                                            border: '1px solid #bdbdbd',
                                            boxShadow: 'none',
                                            '&:hover, &.Mui-focusVisible, &.Mui-active': {
                                                boxShadow: 'none',
                                            },
                                        },
                                        '& .MuiSlider-track': {
                                            width: 36,
                                            borderRadius: 0,
                                            borderColor: 'transparent',
                                            backgroundColor: 'rgba(240, 198, 116, 0.8)',
                                            borderRight: '1px solid #bdbdbd',
                                            borderLeft: '1px solid #bdbdbd',
                                        },
                                        '& .MuiSlider-rail': {
                                            width: 36,
                                            borderRadius: 0,
                                            backgroundColor: 'rgba(230, 230, 230, 0.8)',
                                            borderRight: '1px solid #bdbdbd',
                                            borderLeft: '1px solid #bdbdbd',
                                        },
                                    }}
                                />
                            </Box>
                        ))}
                    </Box>
                </Box>
            </Box>

            {/* Row 3: Value displays */}
            <Box sx={{ display: 'flex', mt: 2, pl: `${yAxisWidth + chartGap}px` }}>
                <Box sx={{ flex: 1, display: 'flex', justifyContent: 'space-around' }}>
                    {resourcesInCurrentTrial?.slice(1).map((resId) => (
                        <Box key={resId} sx={{ width: 120, textAlign: 'center' }}>
                            <Typography>{ratings[resId] ?? 100}</Typography>
                        </Box>
                    ))}
                </Box>
            </Box>
        </Box>
    );
}

export default SimilarityQuestionnaire; 