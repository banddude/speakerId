"use client"

import { useState, useEffect } from "react"
import { User, UserCheck, UserX, Edit, Percent, Search, Filter, BarChart3 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { RenameSpeakerDialog } from "@/components/rename-speaker-dialog"
import { getSpeakers } from "@/lib/api-mock"
import type { Speaker } from "@/types"

export function SpeakerStats() {
  const [speakers, setSpeakers] = useState<Speaker[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedSpeaker, setSelectedSpeaker] = useState<Speaker | null>(null)
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSpeakers() {
      try {
        const data = await getSpeakers()
        setSpeakers(data)
      } catch (err) {
        console.error("Error fetching speakers:", err)
        setError("Failed to load speakers")
      } finally {
        setLoading(false)
      }
    }

    fetchSpeakers()
  }, [])

  const filteredSpeakers = speakers.filter((speaker) => speaker.name.toLowerCase().includes(searchQuery.toLowerCase()))

  const knownSpeakers = filteredSpeakers.filter((speaker) => !speaker.isUnknown)
  const unknownSpeakers = filteredSpeakers.filter((speaker) => speaker.isUnknown)

  const openRenameDialog = (speaker: Speaker) => {
    setSelectedSpeaker(speaker)
    setRenameDialogOpen(true)
  }

  return (
    <Card>
      <CardContent className="p-6 space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search speakers..."
              className="pl-8"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex gap-2 text-sm">
            <div className="flex items-center gap-1 px-2 py-1 bg-muted rounded-md">
              <User className="h-4 w-4" />
              <span>Total: {speakers.length}</span>
            </div>
            <div className="flex items-center gap-1 px-2 py-1 bg-muted rounded-md">
              <UserCheck className="h-4 w-4" />
              <span>Known: {knownSpeakers.length}</span>
            </div>
            <div className="flex items-center gap-1 px-2 py-1 bg-muted rounded-md">
              <UserX className="h-4 w-4" />
              <span>Unknown: {unknownSpeakers.length}</span>
            </div>
          </div>

          <Button variant="outline" size="sm">
            <BarChart3 className="h-4 w-4 mr-2" />
            View Analytics
          </Button>
        </div>

        <Tabs defaultValue="all">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="all">All Speakers</TabsTrigger>
            <TabsTrigger value="known">Known</TabsTrigger>
            <TabsTrigger value="unknown">Unknown</TabsTrigger>
          </TabsList>

          {loading ? (
            <div className="space-y-3 mt-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center p-3 border rounded-lg">
                  <Skeleton className="h-10 w-10 rounded-full mr-3" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-8 text-muted-foreground mt-4">{error}</div>
          ) : (
            <>
              <TabsContent value="all" className="mt-4 space-y-3 max-h-[400px] overflow-y-auto pr-1">
                {filteredSpeakers.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    {searchQuery ? "No matching speakers found" : "No speakers found"}
                  </div>
                ) : (
                  filteredSpeakers.map((speaker) => (
                    <SpeakerItem key={speaker.id} speaker={speaker} onRename={() => openRenameDialog(speaker)} />
                  ))
                )}
              </TabsContent>

              <TabsContent value="known" className="mt-4 space-y-3 max-h-[400px] overflow-y-auto pr-1">
                {knownSpeakers.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    {searchQuery ? "No matching known speakers found" : "No known speakers found"}
                  </div>
                ) : (
                  knownSpeakers.map((speaker) => (
                    <SpeakerItem key={speaker.id} speaker={speaker} onRename={() => openRenameDialog(speaker)} />
                  ))
                )}
              </TabsContent>

              <TabsContent value="unknown" className="mt-4 space-y-3 max-h-[400px] overflow-y-auto pr-1">
                {unknownSpeakers.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    {searchQuery ? "No matching unknown speakers found" : "No unknown speakers found"}
                  </div>
                ) : (
                  unknownSpeakers.map((speaker) => (
                    <SpeakerItem key={speaker.id} speaker={speaker} onRename={() => openRenameDialog(speaker)} />
                  ))
                )}
              </TabsContent>
            </>
          )}
        </Tabs>
      </CardContent>

      {selectedSpeaker && (
        <RenameSpeakerDialog
          open={renameDialogOpen}
          onOpenChange={setRenameDialogOpen}
          speakerName={selectedSpeaker.name}
          isUnknown={selectedSpeaker.isUnknown}
        />
      )}
    </Card>
  )
}

function SpeakerItem({
  speaker,
  onRename,
}: {
  speaker: Speaker
  onRename: () => void
}) {
  return (
    <div
      className={`flex items-center p-3 border rounded-lg ${
        speaker.isUnknown
          ? "border-yellow-200 bg-yellow-50 dark:bg-yellow-950/20 dark:border-yellow-900"
          : "hover:bg-muted/50"
      } transition-colors`}
    >
      <Avatar className="h-9 w-9 mr-3">
        <AvatarFallback className={speaker.isUnknown ? "bg-yellow-100 text-yellow-900" : ""}>
          {speaker.name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()}
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <div className="flex items-center">
          <p className="text-sm font-medium truncate">{speaker.name}</p>
          {speaker.isUnknown && (
            <span className="ml-2 inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200">
              Unknown
            </span>
          )}
        </div>
        <div className="flex text-xs text-muted-foreground">
          <span>{speaker.appearances || 0} appearances</span>
          {!speaker.isUnknown && speaker.confidence !== undefined && (
            <>
              <span className="mx-2">•</span>
              <span className="flex items-center">
                <Percent className="h-3 w-3 mr-1" />
                {speaker.confidence}% confidence
              </span>
            </>
          )}
        </div>
      </div>
      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onRename}>
        <Edit className="h-4 w-4" />
      </Button>
    </div>
  )
}

