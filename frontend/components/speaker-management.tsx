"use client"

import { useState } from "react"
import { UserCheck, UserX, Edit, Percent } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"

// Mock data - in a real app, this would come from your API
const speakersData = [
  { id: 1, name: "John Smith", matchCount: 42, isUnknown: false, confidence: 92 },
  { id: 2, name: "Sarah Johnson", matchCount: 38, isUnknown: false, confidence: 88 },
  { id: 3, name: "Unknown Speaker 1", matchCount: 15, isUnknown: true, confidence: 0 },
  { id: 4, name: "Michael Brown", matchCount: 27, isUnknown: false, confidence: 76 },
]

export function SpeakerManagement() {
  const [speakers, setSpeakers] = useState(speakersData)
  const [selectedSpeaker, setSelectedSpeaker] = useState<(typeof speakersData)[0] | null>(null)
  const [newName, setNewName] = useState("")
  const [dialogOpen, setDialogOpen] = useState(false)

  const handleRename = () => {
    if (!selectedSpeaker || !newName.trim()) return

    setSpeakers(
      speakers.map((speaker) =>
        speaker.id === selectedSpeaker.id ? { ...speaker, name: newName, isUnknown: false } : speaker,
      ),
    )

    setDialogOpen(false)
    setNewName("")
  }

  const openRenameDialog = (speaker: (typeof speakersData)[0]) => {
    setSelectedSpeaker(speaker)
    setNewName(speaker.name)
    setDialogOpen(true)
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-medium">Speakers in Database</h3>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <UserCheck className="h-4 w-4 mr-2" />
            Merge Speakers
          </Button>
        </div>
      </div>

      <div className="space-y-3">
        {speakers.map((speaker) => (
          <div
            key={speaker.id}
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
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openRenameDialog(speaker)}>
              <Edit className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Speaker</DialogTitle>
            <DialogDescription>
              {selectedSpeaker?.isUnknown
                ? "Assign a name to this unknown speaker"
                : "Update the name for this speaker"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Speaker Name</Label>
              <Input
                id="name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Enter speaker name"
              />
            </div>
            {selectedSpeaker?.isUnknown && (
              <div className="rounded-md bg-yellow-50 p-4 dark:bg-yellow-950/20">
                <div className="flex">
                  <UserX className="h-5 w-5 text-yellow-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Unknown Speaker</h3>
                    <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
                      <p>
                        Assigning a name will update all instances where this speaker was detected with at least 70%
                        similarity.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleRename}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

