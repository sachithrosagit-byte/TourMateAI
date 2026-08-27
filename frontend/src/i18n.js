import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enTranslations from './locales/en.json';
import siTranslations from './locales/si.json';
import itTranslations from './locales/it.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: {
        translation: enTranslations
      },
      si: {
        translation: siTranslations
      },
      it: {
        translation: itTranslations
      }
    },
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already escapes values
    }
  });

export default i18n;
