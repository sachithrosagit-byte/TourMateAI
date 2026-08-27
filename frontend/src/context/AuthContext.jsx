// Auth state for the whole app.
//
// Wraps Firebase email/password auth and keeps two things in sync:
//   - `firebaseUser`: the raw Firebase user (source of the ID token)
//   - `backendUser` : the matching Users row returned by POST /api/auth/verify
//
// `onAuthStateChanged` is the single sync point: whenever Firebase auth changes
// (sign-in, sign-up, sign-out, token refresh on reload) we upsert/fetch the DB
// user. `loading` guards the first resolution so ProtectedRoute doesn't bounce a
// user who is actually logged in but not yet confirmed.

import { createContext, useContext, useEffect, useState } from 'react'
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signOut,
} from 'firebase/auth'
import { auth } from '../firebase'
import api from '../services/api'

const AuthContext = createContext(null)

// Turn Firebase's error codes into human-readable messages for the forms.
function friendlyAuthError(err) {
  const code = err?.code || ''
  switch (code) {
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
    case 'auth/user-not-found':
      return 'Incorrect email or password.'
    case 'auth/email-already-in-use':
      return 'An account with that email already exists. Try logging in.'
    case 'auth/weak-password':
      return 'Password is too weak — use at least 6 characters.'
    case 'auth/invalid-email':
      return 'Please enter a valid email address.'
    case 'auth/too-many-requests':
      return 'Too many attempts. Please wait a moment and try again.'
    default:
      return err?.message || 'Something went wrong. Please try again.'
  }
}

export function AuthProvider({ children }) {
  const [firebaseUser, setFirebaseUser] = useState(null)
  const [backendUser, setBackendUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fires immediately with the current user (or null) and on every change.
    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      setFirebaseUser(fbUser)
      if (fbUser) {
        try {
          // Interceptor attaches the token; backend creates/fetches the DB row.
          const { data } = await api.post('/auth/verify')
          setBackendUser(data.user)
        } catch (err) {
          console.error('Backend auth verify failed:', err)
          setBackendUser(null)
        }
      } else {
        setBackendUser(null)
      }
      setLoading(false)
    })
    return unsubscribe
  }, [])

  // These throw a friendly Error on failure; the pages catch and display it.
  async function signup(email, password) {
    try {
      await createUserWithEmailAndPassword(auth, email, password)
    } catch (err) {
      throw new Error(friendlyAuthError(err))
    }
  }

  async function login(email, password) {
    try {
      await signInWithEmailAndPassword(auth, email, password)
    } catch (err) {
      throw new Error(friendlyAuthError(err))
    }
  }

  async function logout() {
    await signOut(auth)
  }

  const value = {
    firebaseUser,
    user: backendUser,
    // Let pages push a fresh user row into context (e.g. after saving the
    // Profile) so the navbar/dashboard greeting stay in sync without a reload.
    setUser: setBackendUser,
    loading,
    isAuthenticated: !!firebaseUser,
    signup,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
