"use client"

import { useState } from "react"
import { Edit, Percent, Search, Filter } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { RenameSpeakerDialog } from "@/components/rename-speaker-dialog"

// Mock data - in a real app, this would come from your API
const speakersData = [
  { id: 1, name: "John Smith", matchCount: 42, isUnknown: false, confidence: 92 },
  { id: 2, name: "Sarah Johnson", matchCount: 38, isUnknown: false, confidence: 88 },
  { id: 3, name: "Unknown Speaker 1", matchCount: 15, isUnknown: true, confidence: 0 },
  { id: 4, name: "Michael Brown", matchCount: 27, isUnknown: false, confidence: 76 },
  { id: 5, name: "Unknown Speaker 2", matchCount: 8, isUnknown: true, confidence: 0 },
]

export function SpeakerDatabase() {
  const [speakers, setSpeakers] = useState(speakersData)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedSpeaker, setSelectedSpeaker] = useState<(typeof speakersData)[0] | null>(null)
  const [renameDialogOpen, setRenameDialogOpen] = useState(false)

  const filteredSpeakers = speakers.filter((speaker) => speaker.name.toLowerCase().includes(searchQuery.toLowerCase()))

  const knownSpeakers = filteredSpeakers.filter((speaker) => !speaker.isUnknown)
  const unknownSpeakers = filteredSpeakers.filter((speaker) => speaker.isUnknown)

  const openRenameDialog = (speaker: (typeof speakersData)[0]) => {
    setSelectedSpeaker(speaker)
    setRenameDialogOpen(true)
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Speaker Database</CardTitle>
        <CardDescription>Manage identified and unknown speakers</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
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

        <Tabs defaultValue="all">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="all">All ({filteredSpeakers.length})</TabsTrigger>
            <TabsTrigger value="known">Known ({knownSpeakers.length})</TabsTrigger>
            <TabsTrigger value="unknown">Unknown ({unknownSpeakers.length})</TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-4 space-y-3 max-h-[400px] overflow-y-auto pr-1">
            {filteredSpeakers.map((speaker) => (
              <SpeakerItem key={speaker.id} speaker={speaker} onRename={() => openRenameDialog(speaker)} />
            ))}
          </TabsContent>

          <TabsContent value="known" className="mt-4 space-y-3 max-h-[400px] overflow-y-auto pr-1">
            {knownSpeakers.map((speaker) => (
              <SpeakerItem key={speaker.id} speaker={speaker} onRename={() => openRenameDialog(speaker)} />
            ))}
          </TabsContent>

          <TabsContent value="unknown" className="mt-4 space-y-3 max-h-[400px] overflow-y-auto pr-1">
            {unknownSpeakers.map((speaker) => (
              <SpeakerItem key={speaker.id} speaker={speaker} onRename={() => openRenameDialog(speaker)} />
            ))}
          </TabsContent>
        </Tabs>
      </CardContent>

      {selectedSpeaker && (
        <RenameSpeakerDialog
          open={renameDialogOpen}
          onOpenChange={setRenameDialogOpen}
          speakerName={selectedSpeaker.name}
        />
      )}
    </Card>
  )
}

function SpeakerItem({
  speaker,
  onRename,
}: {
  speaker: (typeof speakersData)[0]
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
          <span>{speaker.matchCount} appearances</span>
          {!speaker.isUnknown && (
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

