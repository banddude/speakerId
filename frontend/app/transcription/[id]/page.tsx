"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Play, Pause, SkipBack, SkipForward, Edit2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Slider } from "@/components/ui/slider"
import { RenameSpeakerDialog } from "@/components/rename-speaker-dialog"

// This would be fetched from your API in a real application
const mockTranscription = {
  id: "123",
  filename: "team_meeting_march12.wav",
  duration: 325, // seconds
  segments: [
    {
      id: 1,
      speaker: "John Smith",
      text: "Good morning everyone. Let's discuss the quarterly results.",
      timestamp: 15,
      duration: 5,
      confidence: 92,
    },
    {
      id: 2,
      speaker: "Sarah Johnson",
      text: "I've prepared a presentation with the key metrics.",
      timestamp: 22,
      duration: 4,
      confidence: 88,
    },
    {
      id: 3,
      speaker: "Unknown Speaker 1",
      text: "Can we also talk about the new product launch timeline?",
      timestamp: 35,
      duration: 6,
      confidence: 0,
    },
    {
      id: 4,
      speaker: "John Smith",
      text: "Yes, we'll get to that after the financial overview.",
      timestamp: 42,
      duration: 5,
      confidence: 94,
    },
    {
      id: 5,
      speaker: "Michael Brown",
      text: "I have some updates on the marketing campaign as well.",
      timestamp: 50,
      duration: 7,
      confidence: 76,
    },
  ],
}

export default function TranscriptionPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [selectedSpeaker, setSelectedSpeaker] = useState("")

  // In a real app, you would fetch the transcription data based on the ID
  const transcription = mockTranscription

  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= transcription.duration) {
            setIsPlaying(false)
            return transcription.duration
          }
          return prev + 1
        })
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [isPlaying, transcription.duration])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const togglePlayback = () => {
    setIsPlaying(!isPlaying)
  }

  const handleRenameClick = (speaker: string) => {
    setSelectedSpeaker(speaker)
    setRenameDialogOpen(true)
  }

  const isCurrentSegment = (timestamp: number, duration: number) => {
    return currentTime >= timestamp && currentTime < timestamp + duration
  }

  return (
    <div className="container max-w-4xl py-8">
      <Button variant="ghost" onClick={() => router.push("/")} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Dashboard
      </Button>

      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{transcription.filename}</h1>
          <p className="text-muted-foreground">Transcription ID: {params.id}</p>
        </div>

        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{formatTime(currentTime)}</span>
              <span className="text-sm text-muted-foreground">{formatTime(transcription.duration)}</span>
            </div>

            <Slider
              value={[currentTime]}
              max={transcription.duration}
              step={1}
              onValueChange={(value) => setCurrentTime(value[0])}
              className="cursor-pointer"
            />

            <div className="flex justify-center space-x-2">
              <Button variant="outline" size="icon" onClick={() => setCurrentTime(Math.max(0, currentTime - 10))}>
                <SkipBack className="h-4 w-4" />
              </Button>
              <Button onClick={togglePlayback} size="icon">
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCurrentTime(Math.min(transcription.duration, currentTime + 10))}
              >
                <SkipForward className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Transcript</h2>

          {transcription.segments.map((segment) => (
            <div
              key={segment.id}
              className={`flex gap-4 p-3 rounded-lg transition-colors ${
                isCurrentSegment(segment.timestamp, segment.duration) ? "bg-primary/10" : "hover:bg-muted/50"
              }`}
            >
              <div className="flex-shrink-0 pt-1">
                <Avatar className="h-8 w-8">
                  <AvatarFallback
                    className={segment.speaker.includes("Unknown") ? "bg-yellow-100 text-yellow-900" : ""}
                  >
                    {segment.speaker
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                      .toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center">
                  <span className="text-sm font-medium">{segment.speaker}</span>
                  {segment.speaker.includes("Unknown") && (
                    <span className="ml-2 inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
                      Unknown
                    </span>
                  )}
                  <span className="ml-auto text-xs text-muted-foreground">{formatTime(segment.timestamp)}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 ml-2"
                    onClick={() => handleRenameClick(segment.speaker)}
                  >
                    <Edit2 className="h-3 w-3" />
                  </Button>
                </div>
                <p className="text-sm">{segment.text}</p>
                {!segment.speaker.includes("Unknown") && (
                  <div className="text-xs text-muted-foreground">Match confidence: {segment.confidence}%</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <RenameSpeakerDialog
        open={renameDialogOpen}
        onOpenChange={setRenameDialogOpen}
        speakerName={selectedSpeaker}
        transcriptionId={params.id}
      />
    </div>
  )
}

