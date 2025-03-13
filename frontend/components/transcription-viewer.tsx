"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Play, Pause, SkipBack, SkipForward } from "lucide-react"

// This would be fetched from your API in a real application
const mockTranscription = [
  {
    id: 1,
    speaker: "John Smith",
    text: "Good morning everyone. Let's discuss the quarterly results.",
    timestamp: "00:00:15",
    confidence: 92,
  },
  {
    id: 2,
    speaker: "Sarah Johnson",
    text: "I've prepared a presentation with the key metrics.",
    timestamp: "00:00:22",
    confidence: 88,
  },
  {
    id: 3,
    speaker: "Unknown Speaker 1",
    text: "Can we also talk about the new product launch timeline?",
    timestamp: "00:00:35",
    confidence: 0,
  },
  {
    id: 4,
    speaker: "John Smith",
    text: "Yes, we'll get to that after the financial overview.",
    timestamp: "00:00:42",
    confidence: 94,
  },
  {
    id: 5,
    speaker: "Michael Brown",
    text: "I have some updates on the marketing campaign as well.",
    timestamp: "00:00:50",
    confidence: 76,
  },
]

export function TranscriptionViewer() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)

  const togglePlayback = () => {
    setIsPlaying(!isPlaying)
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Transcription</CardTitle>
        <CardDescription>Team Meeting - March 10, 2025</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex justify-center space-x-2">
          <Button variant="outline" size="icon">
            <SkipBack className="h-4 w-4" />
          </Button>
          <Button onClick={togglePlayback} size="icon">
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
          <Button variant="outline" size="icon">
            <SkipForward className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-4">
          {mockTranscription.map((segment) => (
            <div key={segment.id} className="flex gap-4">
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
                  <span className="ml-auto text-xs text-muted-foreground">{segment.timestamp}</span>
                </div>
                <p className="text-sm">{segment.text}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

