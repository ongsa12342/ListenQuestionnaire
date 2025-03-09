import React, { useState, useEffect } from "react";
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
import Cookies from "js-cookie"; // Import Cookies
import { useTranslation } from "react-i18next";

function LandingPage({ onStart }) {
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

        onStart(name);
    };

    const handleLanguageChange = (lng) => {
        i18n.changeLanguage(lng);
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

            <Box sx={{ textAlign: "left", mb: 4, p: 3, border: "1px solid #ccc", borderRadius: 2 }}>
                <Typography variant="h4" gutterBottom>
                    {t("landingPage.title")}
                </Typography>

                <Typography
                    variant="body1"
                    sx={{ mb: 2 }}
                    dangerouslySetInnerHTML={{ __html: t("landingPage.description") }}
                />

                <ul style={{ margin: 0, paddingLeft: "1.25rem", marginBottom: "1rem" }}>
                    <li>
                        <strong>{t("landingPage.steps.listen").split(":")[0]}:</strong>
                        {t("landingPage.steps.listen").split(":")[1]}
                    </li>
                    <li
                        dangerouslySetInnerHTML={{
                            __html: `<strong>${t("landingPage.steps.select").split(":")[0]}:</strong> ${t("landingPage.steps.select").split(":")[1]}`
                        }}
                    />
                    <li>
                        <strong>{t("landingPage.steps.submit").split(":")[0]}:</strong>
                        {t("landingPage.steps.submit").split(":")[1]}
                    </li>
                </ul>

                <Typography variant="body1" sx={{ mb: 2 }}>
                    {t("landingPage.finalNote")}
                </Typography>

                <form onSubmit={handleSubmit} style={{ textAlign: "left" }}>
                    <Stack spacing={1}>
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
                                label={<span style={{ fontSize: "0.9rem" }}>{t("landingPage.consentText")}</span>}
                            />
                            {agreeError && (
                                <FormHelperText error>
                                    {t("landingPage.consentError")}
                                </FormHelperText>
                            )}
                        </Box>

                        <Button type="submit" variant="contained" color="primary">
                            {t("landingPage.startButton")}
                        </Button>
                    </Stack>
                </form>
            </Box>
        </Container>
    );
}

export default LandingPage;
