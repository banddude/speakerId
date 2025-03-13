"use client"

import { useRouter } from "next/navigation"
import { FileAudio, MoreHorizontal, Play, Download, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

// Mock data - in a real app, this would come from your API
const recentUploads = [
  { id: "123", name: "team_meeting_march12.wav", date: "2025-03-12", speakers: 4, duration: "45:22" },
  { id: "122", name: "client_interview.wav", date: "2025-03-08", speakers: 2, duration: "32:15" },
  { id: "121", name: "product_discussion.wav", date: "2025-03-05", speakers: 3, duration: "28:47" },
]

export function RecentUploads() {
  const router = useRouter()

  const handleViewTranscription = (id: string) => {
    router.push(`/transcription/${id}`)
  }

  return (
    <div className="space-y-4">
      {recentUploads.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No recent uploads found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {recentUploads.map((upload) => (
            <div
              key={upload.id}
              className="flex items-center p-3 border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <FileAudio className="h-5 w-5 mr-3 text-primary" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{upload.name}</p>
                <div className="flex text-xs text-muted-foreground">
                  <span>{new Date(upload.date).toLocaleDateString()}</span>
                  <span className="mx-2">•</span>
                  <span>{upload.speakers} speakers</span>
                  <span className="mx-2">•</span>
                  <span>{upload.duration}</span>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => handleViewTranscription(upload.id)}
                >
                  <Play className="h-4 w-4" />
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => handleViewTranscription(upload.id)}>
                      View Transcription
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Download className="h-4 w-4 mr-2" />
                      Download Transcript
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

