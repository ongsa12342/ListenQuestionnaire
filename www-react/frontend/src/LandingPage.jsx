import React, { useState } from "react";
import { Container, Box, Typography, TextField, Button, Checkbox, FormControlLabel, FormHelperText, Stack } from "@mui/material";
import { useTranslation } from "react-i18next"; // Import translation hook

function LandingPage({ onStart }) {
    const { t } = useTranslation(); // Use translations
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
            <Box sx={{ textAlign: "left", mb: 4, p: 3, border: "1px solid #ccc", borderRadius: 2 }}>
                <Typography variant="h4" gutterBottom>{t("landingPage.title")}</Typography>
                <Typography variant="body1" sx={{ mb: 2 }}>{t("landingPage.description")}</Typography>

                <Typography variant="subtitle1" sx={{ fontWeight: "bold", mb: 1 }}>{t("landingPage.whatToDo")}</Typography>

                <ul style={{ margin: 0, paddingLeft: "1.25rem", marginBottom: "1rem" }}>
                    <li><strong>{t("landingPage.steps.listen").split(":")[0]}:</strong> {t("landingPage.steps.listen").split(":")[1]}</li>
                    <li><strong>{t("landingPage.steps.select").split(":")[0]}:</strong> {t("landingPage.steps.select").split(":")[1]}</li>
                    <li><strong>{t("landingPage.steps.submit").split(":")[0]}:</strong> {t("landingPage.steps.submit").split(":")[1]}</li>
                </ul>

                <Typography variant="body1" sx={{ mb: 2 }}>{t("landingPage.finalNote")}</Typography>

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
                                control={<Checkbox checked={agreed} onChange={(e) => { setAgreed(e.target.checked); if (e.target.checked) setAgreeError(false); }} />}
                                label={<span style={{ fontSize: "0.9rem" }}>{t("landingPage.consentText")}</span>}
                            />
                            {agreeError && <FormHelperText error>{t("landingPage.consentError")}</FormHelperText>}
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
