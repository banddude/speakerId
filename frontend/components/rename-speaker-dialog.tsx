"use client"

import { useState } from "react"
import { UserCheck } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Slider } from "@/components/ui/slider"
import { renameSpeaker } from "@/lib/api-mock"

interface RenameSpeakerDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  speakerName: string
  isUnknown?: boolean
  conversationId?: string
  segmentIds?: string[]
}

export function RenameSpeakerDialog({
  open,
  onOpenChange,
  speakerName,
  isUnknown = false,
  conversationId,
  segmentIds,
}: RenameSpeakerDialogProps) {
  const [newName, setNewName] = useState(speakerName)
  const [updateAllInstances, setUpdateAllInstances] = useState(true)
  const [confidenceThreshold, setConfidenceThreshold] = useState(70)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRename = async () => {
    if (!newName.trim()) return

    setProcessing(true)
    setError(null)

    try {
      await renameSpeaker(speakerName, newName, updateAllInstances, confidenceThreshold)

      // Success
      onOpenChange(false)

      // In a real app, you would refresh the data here
      // For the mockup, we'll just reload the page after a delay
      setTimeout(() => {
        window.location.reload()
      }, 500)
    } catch (err) {
      console.error("Failed to rename speaker:", err)
      setError(err instanceof Error ? err.message : "Failed to rename speaker")
    } finally {
      setProcessing(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isUnknown ? "Identify Unknown Speaker" : "Rename Speaker"}</DialogTitle>
          <DialogDescription>
            {isUnknown ? "Assign a name to this unknown speaker" : "Update the name for this speaker"}
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

          <div className="flex items-center space-x-2">
            <Checkbox
              id="update-all"
              checked={updateAllInstances}
              onCheckedChange={(checked) => setUpdateAllInstances(checked as boolean)}
            />
            <Label htmlFor="update-all" className="text-sm">
              Update all instances with similarity above threshold
            </Label>
          </div>

          {updateAllInstances && (
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label htmlFor="confidence-threshold" className="text-sm">
                  Confidence Threshold
                </Label>
                <span className="text-sm">{confidenceThreshold}%</span>
              </div>
              <Slider
                id="confidence-threshold"
                min={50}
                max={95}
                step={5}
                value={[confidenceThreshold]}
                onValueChange={(value) => setConfidenceThreshold(value[0])}
              />
              <p className="text-xs text-muted-foreground">
                Only update instances where the match confidence is at least {confidenceThreshold}%
              </p>
            </div>
          )}

          {isUnknown && (
            <div className="rounded-md bg-yellow-50 p-4 dark:bg-yellow-950/20">
              <div className="flex">
                <UserCheck className="h-5 w-5 text-yellow-400" />
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Speaker Identification</h3>
                  <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-300">
                    <p>
                      Assigning a name will update all instances where this speaker was detected with at least{" "}
                      {confidenceThreshold}% similarity.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {error && <div className="text-sm text-red-500">{error}</div>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleRename} disabled={processing}>
            {processing ? "Processing..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

