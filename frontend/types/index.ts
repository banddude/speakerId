// Define types based on expected data structure from Python backend

export interface Speaker {
  id: string
  name: string
  isUnknown: boolean
  confidence?: number
  appearances?: number
}

export interface SpeakerMatch {
  speakerId: string
  speakerName: string
  confidence: number
  isUnknown: boolean
}

export interface TranscriptSegment {
  id: string
  start: number
  end: number
  text: string
  speaker: SpeakerMatch
}

export interface Conversation {
  id: string
  filename: string
  duration: number
  created: string
  segments: TranscriptSegment[]
}

export interface ProcessingStatus {
  id: string
  filename: string
  status: "queued" | "processing" | "completed" | "failed"
  stage?: string
  progress?: number
  error?: string
}

