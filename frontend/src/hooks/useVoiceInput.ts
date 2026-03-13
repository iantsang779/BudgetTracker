import { useCallback, useEffect, useRef, useState } from 'react'
import { parseTranscript } from '../api/voice'
import type { VoiceParseResponse } from '../types'

export interface VoiceInputState {
  supported: boolean
  listening: boolean
  transcript: string
  error: string | null
  parseResult: VoiceParseResponse | null
  isLoading: boolean
  start: () => void
  stop: () => void
  reset: () => void
}

export function useVoiceInput(): VoiceInputState {
  const RecognitionCtor =
    typeof window !== 'undefined'
      ? (window.SpeechRecognition ?? window.webkitSpeechRecognition)
      : undefined

  const supported = RecognitionCtor !== undefined

  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const [listening, setListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [parseResult, setParseResult] = useState<VoiceParseResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
  }, [])

  const reset = useCallback(() => {
    recognitionRef.current?.abort()
    setTranscript('')
    setParseResult(null)
    setError(null)
    setListening(false)
    setIsLoading(false)
  }, [])

  const start = useCallback(() => {
    if (!RecognitionCtor) return

    setError(null)
    setTranscript('')
    setParseResult(null)

    const recognition = new RecognitionCtor()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onstart = () => setListening(true)

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = ''
      let final = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          final += result[0].transcript
        } else {
          interim += result[0].transcript
        }
      }
      setTranscript(final || interim)
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please allow microphone permissions.')
      } else if (event.error === 'no-speech') {
        setError('No speech detected. Please try again.')
      } else {
        setError(`Voice error: ${event.error}`)
      }
      setListening(false)
    }

    recognition.onend = () => {
      setListening(false)
    }

    recognitionRef.current = recognition
    recognition.start()
  }, [RecognitionCtor])

  // Parse transcript when listening ends and we have text
  useEffect(() => {
    if (!listening && transcript && !parseResult && !error) {
      setIsLoading(true)
      parseTranscript(transcript)
        .then((result) => {
          setParseResult(result)
        })
        .catch(() => {
          setError('Failed to parse transcript. Please try again.')
        })
        .finally(() => {
          setIsLoading(false)
        })
    }
  }, [listening, transcript, parseResult, error])

  useEffect(() => {
    return () => {
      recognitionRef.current?.abort()
    }
  }, [])

  return { supported, listening, transcript, error, parseResult, isLoading, start, stop, reset }
}
