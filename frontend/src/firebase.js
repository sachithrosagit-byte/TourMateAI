// Firebase client initialisation.
//
// Reads the public Firebase web config from VITE_ env vars (see .env.example) and
// exports a single shared `auth` instance used by the AuthContext and the Axios
// interceptor. This is the ONLY place the Firebase app is initialised.

import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

if (!firebaseConfig.apiKey) {
  // Fail loud in dev rather than silently producing "auth/invalid-api-key".
  console.error(
    'Firebase config missing. Copy frontend/.env.example to frontend/.env and fill in the VITE_FIREBASE_* values.',
  )
}

const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export default app
