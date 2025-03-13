"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { FileAudio, MoreHorizontal, Play, Download, Trash2, Search, Filter, Clock } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Skeleton } from "@/components/ui/skeleton"
import { getConversations } from "@/lib/api-mock"
import type { Conversation } from "@/types"

export function ConversationList() {
  const router = useRouter()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchConversations() {
      try {
        const data = await getConversations()
        setConversations(data)
      } catch (err) {
        console.error("Error fetching conversations:", err)
        setError("Failed to load conversations")
      } finally {
        setLoading(false)
      }
    }

    fetchConversations()
  }, [])

  const filteredConversations = conversations.filter((conversation) =>
    conversation.filename.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  const handleViewConversation = (id: string) => {
    router.push(`/conversation/${id}`)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              className="pl-8"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center p-3 border rounded-lg">
                <Skeleton className="h-10 w-10 rounded-full mr-3" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-8 text-muted-foreground">{error}</div>
        ) : filteredConversations.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            {searchQuery ? "No matching conversations found" : "No conversations found"}
          </div>
        ) : (
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {filteredConversations.map((conversation) => (
              <div
                key={conversation.id}
                className="flex items-center p-3 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                onClick={() => handleViewConversation(conversation.id)}
              >
                <FileAudio className="h-5 w-5 mr-3 text-primary" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{conversation.filename}</p>
                  <div className="flex text-xs text-muted-foreground">
                    <span className="flex items-center">
                      <Clock className="h-3 w-3 mr-1" />
                      {formatDate(conversation.created)}
                    </span>
                    <span className="mx-2">•</span>
                    <span>{conversation.segments.length} segments</span>
                    <span className="mx-2">•</span>
                    <span>{formatDuration(conversation.duration)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleViewConversation(conversation.id)
                    }}
                  >
                    <Play className="h-4 w-4" />
                  </Button>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleViewConversation(conversation.id)}>
                        View Conversation
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
      </CardContent>
    </Card>
  )
}

