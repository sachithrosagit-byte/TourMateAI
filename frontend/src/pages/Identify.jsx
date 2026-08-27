// Identify a Landmark — upload a photo, watch a brief AI "scanning" pass, get
// the recognized landmark with confidence + description, and (when the result
// matches a catalogue attraction) jump straight to its detail page. Past
// uploads load from UploadedImages and render as a history list below.
//
// The scanning phase is deliberately paced: recognition is near-instant today
// (mock), so the result is held back until MIN_SCAN_MS has elapsed — an
// animated scan pass reads as "the model is working" instead of a flicker.

import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PageContainer from '../components/layout/PageContainer'
import AttractionImage from '../components/explore/AttractionImage'
import { scenes } from '../assets/photos'
import { fetchUploadHistory, recognizeImage, uploadedImageUrl } from '../services/images'
import '../styles/identify.css'

// Sample shots fanned out in the dropzone — sets expectations for what the
// model can name.
const EXAMPLE_SCENES = [scenes.sigiriyaGround, scenes.nineArch, scenes.templeOfTooth]

const MAX_FILE_MB = 8 // keep in sync with MAX_CONTENT_LENGTH in backend config.py
const ACCEPT = 'image/jpeg,image/png,image/webp'
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

const MIN_SCAN_MS = 2600
const getScanSteps = (t) => [
  t('identify.scanning'),
  t('identify.detecting'),
  t('identify.matching'),
]
const SCAN_STEP_MS = 900

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

function confidenceTone(confidence, t) {
  if (confidence >= 0.75) return { tone: 'high', label: t('identify.highConf') }
  if (confidence >= 0.5) return { tone: 'mid', label: t('identify.midConf') }
  return { tone: 'low', label: t('identify.lowConf') }
}

/** Confidence as a labelled meter, not a bare number. */
function ConfidenceMeter({ confidence }) {
  const { t } = useTranslation()
  const pct = Math.round((confidence || 0) * 100)
  const { tone, label } = confidenceTone(confidence || 0, t)
  return (
    <div className="idf-confidence">
      <div className="idf-confidence-head">
        <span className={`idf-confidence-label idf-tone-${tone}`}>{label}</span>
        <span className="idf-confidence-pct">{pct}%</span>
      </div>
      <div
        className="idf-meter"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        aria-label="Recognition confidence"
      >
        <div className={`idf-meter-fill idf-fill-${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function CameraIcon() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 8.5A2.5 2.5 0 0 1 6.5 6h1l1.2-1.8A1.5 1.5 0 0 1 9.95 3.5h4.1a1.5 1.5 0 0 1 1.25.7L16.5 6h1A2.5 2.5 0 0 1 20 8.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 16.5v-8Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12.5" r="3.4" stroke="currentColor" strokeWidth="1.7" />
    </svg>
  )
}

/** One past upload. Links to the matched attraction when there is one. */
function HistoryItem({ item }) {
  const { t } = useTranslation()
  const pct = Math.round((item.confidence || 0) * 100)
  const { tone } = confidenceTone(item.confidence || 0, t)
  const date = item.created_at
    ? new Date(item.created_at).toLocaleDateString(undefined, {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : null

  const body = (
    <>
      <img
        className="idf-history-thumb"
        src={uploadedImageUrl(item.image_url)}
        alt={item.identified_name || t('identify.uploadedPhoto')}
        loading="lazy"
      />
      <div className="idf-history-body">
        <span className="idf-history-name">{item.identified_name || t('identify.unknown')}</span>
        <span className="idf-history-meta">
          <span className={`idf-history-pct idf-tone-${tone}`}>{pct}% {t('identify.match')}</span>
          {date && (
            <>
              <span aria-hidden="true"> · </span>
              {date}
            </>
          )}
        </span>
      </div>
      {item.matched_attraction && (
        <svg
          className="idf-history-arrow"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="m9 6 6 6-6 6"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </>
  )

  if (item.matched_attraction) {
    return (
      <Link to={`/explore/${item.matched_attraction.id}`} className="idf-history-item idf-history-link">
        {body}
      </Link>
    )
  }
  return <div className="idf-history-item">{body}</div>
}

export default function Identify() {
  const { t } = useTranslation()
  // idle (dropzone) -> preview (file chosen) -> scanning -> result
  const [phase, setPhase] = useState('idle')
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [scanStep, setScanStep] = useState(0)

  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState(false)

  const inputRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    fetchUploadHistory()
      .then((items) => {
        if (!cancelled) setHistory(items)
      })
      .catch(() => {
        if (!cancelled) setHistoryError(true)
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Object URLs leak unless revoked when replaced / on unmount.
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  // Cycle the status line while "analyzing" so the wait reads as progress.
  useEffect(() => {
    if (phase !== 'scanning') return undefined
    setScanStep(0)
    const timer = setInterval(
      () => setScanStep((step) => Math.min(step + 1, getScanSteps(t).length - 1)),
      SCAN_STEP_MS
    )
    return () => clearInterval(timer)
  }, [phase, t])

  const selectFile = (candidate) => {
    if (!candidate) return
    if (!ALLOWED_TYPES.includes(candidate.type)) {
      setError(t('identify.errorFormat'))
      return
    }
    if (candidate.size > MAX_FILE_MB * 1024 * 1024) {
      setError(`${t('identify.errorSize')} ${MAX_FILE_MB} MB.`)
      return
    }
    setError(null)
    setResult(null)
    setFile(candidate)
    setPreviewUrl(URL.createObjectURL(candidate))
    setPhase('preview')
  }

  const handleInputChange = (event) => {
    selectFile(event.target.files?.[0])
    event.target.value = '' // re-selecting the same file should still fire change
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setDragActive(false)
    selectFile(event.dataTransfer.files?.[0])
  }

  const handleDrag = (active) => (event) => {
    event.preventDefault()
    setDragActive(active)
  }

  const analyze = async () => {
    if (!file || phase === 'scanning') return
    setError(null)
    setPhase('scanning')
    try {
      // Hold the result until the scan animation has had its moment.
      const [data] = await Promise.all([recognizeImage(file), delay(MIN_SCAN_MS)])
      setResult(data)
      setHistory((prev) => [data, ...prev])
      setPhase('result')
    } catch (err) {
      setError(
        err?.response?.data?.error ||
          t('identify.errorAnalyze')
      )
      setPhase('preview')
    }
  }

  const reset = () => {
    setFile(null)
    setPreviewUrl(null)
    setResult(null)
    setError(null)
    setPhase('idle')
  }

  const matched = result?.matched_attraction

  return (
    <PageContainer
      title={t('identify.pageTitle')}
      subtitle={t('identify.pageSubtitle')}
      width="narrow"
    >
      <input
        ref={inputRef}
        id="idf-file-input"
        type="file"
        accept={ACCEPT}
        onChange={handleInputChange}
        hidden
      />

      {phase === 'idle' && (
        <label
          htmlFor="idf-file-input"
          className={`idf-dropzone card ${dragActive ? 'idf-dropzone-active' : ''}`}
          onDragOver={handleDrag(true)}
          onDragLeave={handleDrag(false)}
          onDrop={handleDrop}
        >
          <span className="idf-examples" aria-hidden="true">
            {EXAMPLE_SCENES.map((scene) => (
              <img
                key={scene.src}
                className="idf-example"
                src={scene.src}
                style={{ objectPosition: scene.position }}
                alt=""
              />
            ))}
            <span className="idf-examples-icon">
              <CameraIcon />
            </span>
          </span>
          <span className="idf-dropzone-title">{t('identify.dropTitle')}</span>
          <span className="idf-dropzone-sub">
            {t('identify.dropSubtitle1')} <span className="idf-dropzone-browse">{t('identify.dropSubtitle2')}</span> {t('identify.dropSubtitle3')} {MAX_FILE_MB} MB
          </span>
        </label>
      )}

      {phase !== 'idle' && (
        <div className="idf-stage card">
          <div className={`idf-frame ${phase === 'scanning' ? 'idf-frame-scanning' : ''}`}>
            <img className="idf-preview" src={previewUrl} alt={t('identify.previewAlt')} />
            {phase === 'scanning' && (
              <div className="idf-scan-overlay" aria-hidden="true">
                <div className="idf-scan-line" />
                <span className="idf-corner idf-corner-tl" />
                <span className="idf-corner idf-corner-tr" />
                <span className="idf-corner idf-corner-bl" />
                <span className="idf-corner idf-corner-br" />
              </div>
            )}
          </div>

          {phase === 'preview' && (
            <div className="idf-stage-body">
              {error && <div className="alert alert-error">{error}</div>}
              <div className="idf-actions">
                <button type="button" className="btn btn-primary btn-lg" onClick={analyze}>
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M12 3.5 13.8 8.7l5.2 1.8-5.2 1.8L12 17.5l-1.8-5.2L5 10.5l5.2-1.8L12 3.5Z"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M18.5 15.5l.9 2.6 2.6.9-2.6.9-.9 2.6-.9-2.6-2.6-.9 2.6-.9.9-2.6Z"
                      fill="currentColor"
                    />
                  </svg>
                  {t('identify.identifyBtn')}
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => inputRef.current?.click()}
                >
                  {t('identify.chooseDiffBtn')}
                </button>
              </div>
            </div>
          )}

          {phase === 'scanning' && (
            <div className="idf-stage-body idf-scan-steps" role="status">
              {getScanSteps(t).map((step, i) => (
                <span
                  key={step}
                  className={`idf-scan-step${
                    i < scanStep ? ' is-done' : i === scanStep ? ' is-current' : ''
                  }`}
                >
                  <span className="idf-scan-step-icon" aria-hidden="true">
                    {i < scanStep ? (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                        <path
                          d="m5 12 5 5 9-10"
                          stroke="currentColor"
                          strokeWidth="2.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    ) : (
                      <span className="idf-scan-dot" />
                    )}
                  </span>
                  {step}
                </span>
              ))}
            </div>
          )}

          {phase === 'result' && result && (
            <div className="idf-stage-body idf-result">
              <div className="idf-result-head">
                <span className="badge badge-primary idf-result-badge">
                  {t('identify.aiBadge')}
                </span>
                <h2 className="idf-result-name">{result.identified_name}</h2>
              </div>

              <ConfidenceMeter confidence={result.confidence} />

              {result.description && (
                <p className="idf-result-desc">{result.description}</p>
              )}

              {matched && (
                <Link to={`/explore/${matched.id}`} className="idf-match">
                  <AttractionImage attraction={matched} className="idf-match-img" />
                  <span className="idf-match-body">
                    <span className="idf-match-kicker">{t('identify.catalogueBadge')}</span>
                    <span className="idf-match-name">{matched.name}</span>
                    <span className="idf-match-meta">
                      {matched.category} · {t('identify.tapForDetails')}
                    </span>
                  </span>
                  <svg
                    className="idf-match-arrow"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    aria-hidden="true"
                  >
                    <path
                      d="m9 6 6 6-6 6"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </Link>
              )}

              <div className="idf-actions">
                <button type="button" className="btn btn-secondary" onClick={reset}>
                  {t('identify.identifyAnotherBtn')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      <section className="idf-history" aria-label={t('identify.historyTitle')}>
        <h2 className="idf-history-title">{t('identify.historyTitle')}</h2>
        {historyLoading ? (
          <div className="idf-history-state">
            <div className="spinner" />
          </div>
        ) : historyError ? (
          <div className="alert alert-error">
            {t('identify.historyError')}
          </div>
        ) : history.length === 0 ? (
          <p className="idf-history-empty">
            {t('identify.historyEmpty')}
          </p>
        ) : (
          <div className="idf-history-list">
            {history.map((item) => (
              <HistoryItem key={item.id} item={item} />
            ))}
          </div>
        )}
      </section>
    </PageContainer>
  )
}
