import client from './client'
import type { VoiceParseResponse } from '../types'

export async function parseTranscript(transcript: string): Promise<VoiceParseResponse> {
  const res = await client.post<VoiceParseResponse>('/voice/parse', { transcript })
  return res.data
}
