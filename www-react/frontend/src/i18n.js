import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
// import th from "./locales/th.json";

i18n.use(initReactI18next).init({
    resources: {
        en: { translation: en },
        // th: { translation: th }
    },
    lng: "en", // Default language
    fallbackLng: "en", // Fallback to English if no translation found
    interpolation: { escapeValue: false }
});

export default i18n;
