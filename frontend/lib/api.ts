import type { Conversation, Speaker, ProcessingStatus } from "@/types"

// API URL configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api"

// Helper to check if API is available
let apiAvailabilityChecked = false;
let apiAvailable = false;

export async function checkApiAvailability(): Promise<boolean> {
  if (apiAvailabilityChecked) return apiAvailable;
  
  try {
    const response = await fetch(`${API_URL}/conversations`, { 
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      // Short timeout for quicker feedback
      signal: AbortSignal.timeout(3000)
    });
    apiAvailable = response.ok;
    console.log(`API connection ${apiAvailable ? 'successful' : 'failed'}: ${API_URL}`);
  } catch (error) {
    console.error('API connection error:', error);
    apiAvailable = false;
  }
  
  apiAvailabilityChecked = true;
  return apiAvailable;
}

/**
 * Upload and process an audio file
 */
export async function processAudioFile(file: File): Promise<ProcessingStatus> {
  const formData = new FormData()
  formData.append("file", file)

  const response = await fetch(`${API_URL}/process`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || "Failed to process audio file")
  }

  return response.json()
}

/**
 * Get processing status
 */
export async function getProcessingStatus(id: string): Promise<ProcessingStatus> {
  const response = await fetch(`${API_URL}/process/${id}`)

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || "Failed to get processing status")
  }

  return response.json()
}

/**
 * Get all conversations
 */
export async function getConversations(): Promise<Conversation[]> {
  // Check API availability first
  const isAvailable = await checkApiAvailability();
  if (!isAvailable) {
    console.warn('API not available, returning mock data');
    // You could return mock data here if the API is unavailable
    return [];
  }

  const response = await fetch(`${API_URL}/conversations`)

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || "Failed to fetch conversations")
  }

  return response.json()
}

/**
 * Get a specific conversation
 */
export async function getConversation(id: string): Promise<Conversation> {
  const response = await fetch(`${API_URL}/conversations/${id}`)

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || "Failed to fetch conversation")
  }

  return response.json()
}

/**
 * Get all speakers
 */
export async function getSpeakers(): Promise<Speaker[]> {
  const response = await fetch(`${API_URL}/speakers`)

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || "Failed to fetch speakers")
  }

  return response.json()
}

/**
 * Rename a speaker
 */
export async function renameSpeaker(
  originalName: string,
  newName: string,
  updateAllInstances = true,
  minConfidence = 70,
): Promise<{ success: boolean; updated: number }> {
  const response = await fetch(`${API_URL}/speakers/rename`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      originalName,
      newName,
      updateAllInstances,
      minConfidence,
    }),
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || "Failed to rename speaker")
  }

  return response.json()
}

/**
 * Update speaker in a specific conversation
 */
export async function updateConversationSpeaker(
  conversationId: string,
  segmentIds: string[],
  speakerName: string,
): Promise<{ success: boolean }> {
  const response = await fetch(`${API_URL}/conversations/${conversationId}/speakers`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      segmentIds,
      speakerName,
    }),
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || "Failed to update conversation speaker")
  }

  return response.json()
}

/**
 * Get audio URL for a conversation or segment
 */
export function getAudioUrl(conversationId: string, segmentId?: string): string {
  if (segmentId) {
    return `${API_URL}/audio/${conversationId}/segments/${segmentId}`
  }
  return `${API_URL}/audio/${conversationId}`
}

