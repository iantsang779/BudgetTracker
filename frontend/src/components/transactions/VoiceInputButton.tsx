import { useEffect } from 'react'
import { useVoiceInput } from '../../hooks/useVoiceInput'
import type { VoiceParseResponse } from '../../types'

interface VoiceInputButtonProps {
  onParsed: (result: VoiceParseResponse) => void
}

const MicIcon = ({ color = '#cdd6f4' }: { color?: string }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill={color} xmlns="http://www.w3.org/2000/svg">
    <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Z" />
    <path d="M19 11a1 1 0 0 0-2 0 5 5 0 0 1-10 0 1 1 0 0 0-2 0 7 7 0 0 0 6 6.92V20H9a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2h-2v-2.08A7 7 0 0 0 19 11Z" />
  </svg>
)

export default function VoiceInputButton({ onParsed }: VoiceInputButtonProps) {
  const { supported, listening, transcript, error, parseResult, isLoading, start, stop, reset } =
    useVoiceInput()

  // Forward parsed result to parent after render, then reset the hook state
  useEffect(() => {
    if (parseResult && !isLoading) {
      onParsed(parseResult)
      reset()
    }
  }, [parseResult, isLoading, onParsed, reset])

  if (!supported) {
    return (
      <button
        disabled
        title="Voice input is not supported in this browser"
        style={{
          background: '#313244',
          border: '1px solid #45475a',
          borderRadius: 6,
          padding: '6px 12px',
          color: '#6c7086',
          cursor: 'not-allowed',
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <MicIcon color="#6c7086" />
        Voice (unsupported)
      </button>
    )
  }

  const buttonLabel = listening ? 'Stop Recording' : isLoading ? 'Parsing…' : 'Record Transaction'
  const buttonBg = listening ? '#f38ba8' : isLoading ? '#313244' : '#89b4fa'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
      <button
        type="button"
        onClick={listening ? stop : start}
        disabled={isLoading}
        style={{
          background: buttonBg,
          border: 'none',
          borderRadius: 6,
          padding: '6px 12px',
          color: '#1e1e2e',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          fontSize: 13,
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          transition: 'background 0.15s',
        }}
      >
        <MicIcon color="#1e1e2e" />
        {buttonLabel}
        {listening && (
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#1e1e2e',
              animation: 'pulse 1s infinite',
            }}
          />
        )}
      </button>

      {transcript && (
        <span style={{ fontSize: 11, color: '#a6adc8', maxWidth: 260, textAlign: 'right' }}>
          "{transcript}"
        </span>
      )}

      {error && <span style={{ fontSize: 11, color: '#f38ba8' }}>{error}</span>}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  )
}
