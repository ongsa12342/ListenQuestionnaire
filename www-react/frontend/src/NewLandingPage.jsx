import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Button,
    Container,
    Typography,
    TextField,
    Checkbox,
    FormControlLabel,
    FormHelperText,
    Stack,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import Cookies from 'js-cookie';

function NewLandingPage() {
    const navigate = useNavigate();
    const { t, i18n } = useTranslation();
    const [name, setName] = useState("");
    const [error, setError] = useState(false);
    const [agreed, setAgreed] = useState(false);
    const [agreeError, setAgreeError] = useState(false);

    // Load participant name from cookie if it exists
    useEffect(() => {
        const savedName = Cookies.get("participantName");
        if (savedName) {
            setName(savedName);
        }
    }, []);

    // Load language from cookie if it exists
    useEffect(() => {
        const savedLang = Cookies.get("lang");
        if (savedLang) {
            i18n.changeLanguage(savedLang);
        }
    }, [i18n]);

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

        // Save the participant name in a cookie (expires in 7 days)
        Cookies.set("participantName", name, { expires: 7 });

        // Navigate to the questionnaire
        navigate('/ex2/questionnaire');
    };

    const handleLanguageChange = (lng) => {
        i18n.changeLanguage(lng);
        Cookies.set("lang", lng, { expires: 7 });
    };

    return (
        <Container maxWidth="sm" sx={{ mt: 5 }}>
            {/* Language Selection */}
            <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2 }}>
                <Button variant="outlined" onClick={() => handleLanguageChange("en")}>
                    EN
                </Button>
                <Button
                    variant="outlined"
                    onClick={() => handleLanguageChange("th")}
                    sx={{ ml: 1 }}
                >
                    TH
                </Button>
            </Box>

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
                    {t('similarityAssessment.title')}
                </Typography>

                <Typography
                    variant="body1"
                    sx={{ mb: 2 }}
                >
                    {t('similarityAssessment.description')}
                </Typography>

                <ul
                    style={{
                        margin: 0,
                        paddingLeft: "1.25rem",
                        marginBottom: "1rem",
                    }}
                >
                    <li>
                        <strong>{t('similarityAssessment.steps.listen.title')}</strong>
                        <Typography component="div" variant="body2">
                            {t('similarityAssessment.steps.listen.instruction1')}
                            <br />
                            {t('similarityAssessment.steps.listen.instruction2')}
                        </Typography>
                    </li>
                    <li>
                        <strong>{t('similarityAssessment.steps.rate.title')}</strong>
                        <Typography component="div" variant="body2">
                            {t('similarityAssessment.steps.rate.instruction')}
                            <br />
                            <Box sx={{ pl: 2, my: 1 }}>
                                {t('similarityAssessment.steps.rate.scale')}
                            </Box>
                        </Typography>
                    </li>
                    <li>
                        <strong>{t('similarityAssessment.steps.submit.title')}</strong>
                        <Typography component="div" variant="body2">
                            {t('similarityAssessment.steps.submit.instruction1')}
                            <br />
                            {t('similarityAssessment.steps.submit.instruction2')}
                        </Typography>
                    </li>
                </ul>

                <form onSubmit={handleSubmit} style={{ textAlign: "left" }}>
                    <Stack spacing={2}>
                        <TextField
                            label={t("landingPage.nameLabel")}
                            variant="outlined"
                            fullWidth
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            error={error}
                            helperText={error ? t("landingPage.nameError") : ""}
                        />

                        <Box>
                            <FormControlLabel
                                control={
                                    <Checkbox
                                        checked={agreed}
                                        onChange={(e) => {
                                            setAgreed(e.target.checked);
                                            if (e.target.checked) setAgreeError(false);
                                        }}
                                    />
                                }
                                label={
                                    <span style={{ fontSize: "0.9rem" }}>
                                        {t("landingPage.consentText")}
                                    </span>
                                }
                            />
                            {agreeError && (
                                <FormHelperText error>
                                    {t("landingPage.consentError")}
                                </FormHelperText>
                            )}
                        </Box>

                        <Button
                            type="submit"
                            variant="contained"
                            color="primary"
                            fullWidth
                        >
                            {t("landingPage.startButton")}
                        </Button>
                    </Stack>
                </form>
            </Box>
        </Container>
    );
}

export default NewLandingPage; 