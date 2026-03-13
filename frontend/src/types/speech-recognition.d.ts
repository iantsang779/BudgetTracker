// Ambient type declarations for the Web Speech API.
// These are not included in TypeScript's default lib.dom.d.ts.

declare interface SpeechRecognitionAlternative {
  readonly transcript: string
  readonly confidence: number
}

declare interface SpeechRecognitionResult {
  readonly isFinal: boolean
  readonly length: number
  item(index: number): SpeechRecognitionAlternative
  [index: number]: SpeechRecognitionAlternative
}

declare interface SpeechRecognitionResultList {
  readonly length: number
  item(index: number): SpeechRecognitionResult
  [index: number]: SpeechRecognitionResult
}

declare interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number
  readonly results: SpeechRecognitionResultList
}

declare interface SpeechRecognitionErrorEvent extends Event {
  readonly error: string
  readonly message: string
}

declare interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
  onstart: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}

declare interface SpeechRecognitionConstructor {
  new (): SpeechRecognition
}

interface Window {
  SpeechRecognition: SpeechRecognitionConstructor | undefined
  webkitSpeechRecognition: SpeechRecognitionConstructor | undefined
}
