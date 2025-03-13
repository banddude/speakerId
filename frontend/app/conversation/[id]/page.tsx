"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Download, Share, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { RenameSpeakerDialog } from "@/components/rename-speaker-dialog"
import { AudioPlayer } from "@/components/audio-player"
import { getConversation } from "@/lib/api-mock"
import type { Conversation, TranscriptSegment } from "@/types"

export default function ConversationPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [selectedSpeaker, setSelectedSpeaker] = useState("")
  const [selectedSegmentIds, setSelectedSegmentIds] = useState<string[]>([])
  const [playingSegment, setPlayingSegment] = useState<string | null>(null)

  useEffect(() => {
    async function fetchConversation() {
      try {
        const data = await getConversation(params.id)
        setConversation(data)
      } catch (err) {
        console.error("Error fetching conversation:", err)
        setError("Failed to load conversation")
      } finally {
        setLoading(false)
      }
    }

    fetchConversation()
  }, [params.id])

  const handleRenameClick = (speakerName: string, segmentId: string) => {
    setSelectedSpeaker(speakerName)
    setSelectedSegmentIds([segmentId])
    setRenameDialogOpen(true)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const isCurrentSegment = (segment: TranscriptSegment) => {
    return currentTime >= segment.start && currentTime < segment.end
  }

  // Handle main audio player state changes
  const handleMainPlayerStateChange = (playing: boolean) => {
    setIsPlaying(playing)
    if (playing) {
      // When main player starts, stop any segment player
      setPlayingSegment(null)
    }
  }

  // Handle segment player state changes
  const handleSegmentPlayerStateChange = (segmentId: string, playing: boolean) => {
    if (playing) {
      setPlayingSegment(segmentId)
      setIsPlaying(false) // Pause main player when segment plays
    } else if (playingSegment === segmentId) {
      setPlayingSegment(null)
    }
  }

  // Construct audio URL based on conversation ID
  const getAudioUrl = () => {
    // In a real app, this would point to your actual audio file
    // For now, we'll use a mock URL that would be replaced with your actual path
    return `/api/audio/${params.id}`
  }

  if (loading) {
    return (
      <div className="container max-w-4xl py-8 space-y-6">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-10 w-full" />
        <div className="space-y-4">
          <Skeleton className="h-6 w-48" />
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex gap-4">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-1/4" />
                  <Skeleton className="h-3 w-full" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error || !conversation) {
    return (
      <div className="container max-w-4xl py-8">
        <Button variant="ghost" onClick={() => router.push("/")} className="mb-6">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>

        <Card>
          <CardContent className="p-12 text-center">
            <h2 className="text-xl font-semibold mb-2">Error Loading Conversation</h2>
            <p className="text-muted-foreground">{error || "Conversation not found"}</p>
            <Button className="mt-4" onClick={() => router.push("/")}>
              Return to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const audioUrl = getAudioUrl()

  return (
    <div className="container max-w-4xl py-8">
      <Button variant="ghost" onClick={() => router.push("/")} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Dashboard
      </Button>

      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">{conversation.filename}</h1>
          <div className="flex items-center text-muted-foreground">
            <Clock className="h-4 w-4 mr-1" />
            <span>{new Date(conversation.created).toLocaleDateString()}</span>
            <span className="mx-2">•</span>
            <span>{conversation.segments.length} segments</span>
            <span className="mx-2">•</span>
            <span>{formatTime(conversation.duration)}</span>
          </div>
        </div>

        <Card>
          <CardContent className="p-4">
            <AudioPlayer audioUrl={audioUrl} onPlayStateChange={handleMainPlayerStateChange} />

            <div className="flex justify-end gap-2 mt-4">
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button variant="outline" size="sm">
                <Share className="h-4 w-4 mr-2" />
                Share
              </Button>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="transcript">
          <TabsList>
            <TabsTrigger value="transcript">Transcript</TabsTrigger>
            <TabsTrigger value="speakers">Speakers</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
          </TabsList>

          <TabsContent value="transcript" className="mt-4">
            <div className="space-y-4">
              {conversation.segments.map((segment) => (
                <div
                  key={segment.id}
                  className={`flex gap-4 p-3 rounded-lg transition-colors ${
                    isCurrentSegment(segment) && isPlaying
                      ? "bg-primary/10"
                      : playingSegment === segment.id
                        ? "bg-blue-50 dark:bg-blue-950/20"
                        : "hover:bg-muted/50"
                  }`}
                >
                  <div className="flex-shrink-0 pt-1">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className={segment.speaker.isUnknown ? "bg-yellow-100 text-yellow-900" : ""}>
                        {segment.speaker.speakerName
                          .split(" ")
                          .map((n) => n[0])
                          .join("")
                          .toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center">
                      <span className="text-sm font-medium">{segment.speaker.speakerName}</span>
                      {segment.speaker.isUnknown && (
                        <Badge
                          variant="outline"
                          className="ml-2 bg-yellow-100 text-yellow-800 hover:bg-yellow-100 border-yellow-200"
                        >
                          Unknown
                        </Badge>
                      )}
                      <span className="ml-auto text-xs text-muted-foreground">{formatTime(segment.start)}</span>

                      {/* Play segment button */}
                      <AudioPlayer
                        audioUrl={audioUrl}
                        startTime={segment.start}
                        endTime={segment.end}
                        small
                        onPlayStateChange={(playing) => handleSegmentPlayerStateChange(segment.id, playing)}
                      />

                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 ml-1"
                        onClick={() => handleRenameClick(segment.speaker.speakerName, segment.id)}
                      >
                        Rename
                      </Button>
                    </div>
                    <p className="text-sm">{segment.text}</p>
                    {!segment.speaker.isUnknown && (
                      <div className="text-xs text-muted-foreground">
                        Match confidence: {segment.speaker.confidence}%
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="speakers" className="mt-4">
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Speakers in Conversation</h3>

              {/* Group segments by speaker */}
              {Object.entries(
                conversation.segments.reduce(
                  (acc, segment) => {
                    const speakerName = segment.speaker.speakerName
                    if (!acc[speakerName]) {
                      acc[speakerName] = {
                        name: speakerName,
                        isUnknown: segment.speaker.isUnknown,
                        confidence: segment.speaker.confidence,
                        segments: [],
                      }
                    }
                    acc[speakerName].segments.push(segment)
                    return acc
                  },
                  {} as Record<
                    string,
                    { name: string; isUnknown: boolean; confidence: number; segments: TranscriptSegment[] }
                  >,
                ),
              ).map(([name, data]) => (
                <div key={name} className="border rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <Avatar className="h-8 w-8 mr-3">
                      <AvatarFallback className={data.isUnknown ? "bg-yellow-100 text-yellow-900" : ""}>
                        {name
                          .split(" ")
                          .map((n) => n[0])
                          .join("")
                          .toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center">
                        <span className="font-medium">{name}</span>
                        {data.isUnknown && (
                          <Badge
                            variant="outline"
                            className="ml-2 bg-yellow-100 text-yellow-800 hover:bg-yellow-100 border-yellow-200"
                          >
                            Unknown
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {data.segments.length} segments •{!data.isUnknown && ` ${data.confidence}% confidence •`}
                        {formatTime(data.segments.reduce((total, segment) => total + (segment.end - segment.start), 0))}{" "}
                        total speaking time
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="ml-auto"
                      onClick={() => {
                        setSelectedSpeaker(name)
                        setSelectedSegmentIds(data.segments.map((s) => s.id))
                        setRenameDialogOpen(true)
                      }}
                    >
                      Rename
                    </Button>
                  </div>

                  <div className="mt-4 space-y-2">
                    <h4 className="text-sm font-medium">Utterances:</h4>
                    <div className="max-h-40 overflow-y-auto space-y-2 pr-2">
                      {data.segments.map((segment) => (
                        <div
                          key={segment.id}
                          className="flex items-center text-sm p-2 border rounded-md hover:bg-muted/50"
                        >
                          <span className="text-muted-foreground mr-2">{formatTime(segment.start)}</span>
                          <span className="flex-1 truncate">{segment.text}</span>
                          <AudioPlayer
                            audioUrl={audioUrl}
                            startTime={segment.start}
                            endTime={segment.end}
                            small
                            onPlayStateChange={(playing) => handleSegmentPlayerStateChange(segment.id, playing)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="metadata" className="mt-4">
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-medium mb-4">Conversation Metadata</h3>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Filename</p>
                  <p className="text-sm text-muted-foreground">{conversation.filename}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Duration</p>
                  <p className="text-sm text-muted-foreground">{formatTime(conversation.duration)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Created</p>
                  <p className="text-sm text-muted-foreground">{new Date(conversation.created).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Total Segments</p>
                  <p className="text-sm text-muted-foreground">{conversation.segments.length}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Speakers</p>
                  <p className="text-sm text-muted-foreground">
                    {new Set(conversation.segments.map((s) => s.speaker.speakerName)).size}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">Audio File</p>
                  <p className="text-sm text-muted-foreground">
                    <a
                      href={audioUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      Download Original Audio
                    </a>
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      <RenameSpeakerDialog
        open={renameDialogOpen}
        onOpenChange={setRenameDialogOpen}
        speakerName={selectedSpeaker}
        isUnknown={selectedSpeaker.includes("Unknown")}
        conversationId={conversation.id}
        segmentIds={selectedSegmentIds}
      />
    </div>
  )
}

