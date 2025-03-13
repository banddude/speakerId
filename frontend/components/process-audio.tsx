"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { UploadIcon, FileAudio, Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { processAudioFile, getProcessingStatus } from "@/lib/api-mock"
import type { ProcessingStatus } from "@/types"

export function ProcessAudio() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [processing, setProcessing] = useState<boolean>(false)
  const [status, setStatus] = useState<ProcessingStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleProcess = async () => {
    if (!file) return

    setProcessing(true)
    setError(null)

    try {
      // Start processing
      const initialStatus = await processAudioFile(file)
      setStatus(initialStatus)

      // Poll for status updates
      if (initialStatus.status !== "completed" && initialStatus.status !== "failed") {
        const statusInterval = setInterval(async () => {
          try {
            const updatedStatus = await getProcessingStatus(initialStatus.id)
            setStatus(updatedStatus)

            if (updatedStatus.status === "completed" || updatedStatus.status === "failed") {
              clearInterval(statusInterval)
              setProcessing(updatedStatus.status !== "completed")

              if (updatedStatus.status === "completed") {
                // Navigate to the conversation page
                setTimeout(() => {
                  router.push(`/conversation/123`) // Using mock ID for demo
                }, 1000)
              } else if (updatedStatus.status === "failed") {
                setError(updatedStatus.error || "Processing failed")
              }
            }
          } catch (err) {
            clearInterval(statusInterval)
            setProcessing(false)
            setError("Failed to get processing status")
          }
        }, 2000)
      } else if (initialStatus.status === "completed") {
        // Navigate to the conversation page
        setTimeout(() => {
          router.push(`/conversation/123`) // Using mock ID for demo
        }, 1000)
      } else {
        setProcessing(false)
        setError(initialStatus.error || "Processing failed")
      }
    } catch (err) {
      console.error("Error processing audio:", err)
      setProcessing(false)
      setError(err instanceof Error ? err.message : "Failed to process audio")
    }
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Process Audio</CardTitle>
        <CardDescription>Upload and process conversation audio</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center space-y-4">
          {!file ? (
            <div className="flex flex-col items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 w-full">
              <UploadIcon className="h-10 w-10 text-muted-foreground mb-4" />
              <p className="text-sm text-muted-foreground mb-2">Drag and drop or click to upload</p>
              <p className="text-xs text-muted-foreground">Supports MP3, WAV, M4A (max 500MB)</p>
              <input type="file" accept="audio/*" className="hidden" id="audio-upload" onChange={handleFileChange} />
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => document.getElementById("audio-upload")?.click()}
              >
                Select File
              </Button>
            </div>
          ) : (
            <div className="w-full space-y-4">
              <div className="flex items-center p-4 border rounded-lg">
                <FileAudio className="h-8 w-8 mr-4 text-primary" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
              </div>

              {status && processing && (
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>{status.stage || "Processing..."}</span>
                    <span>{status.progress !== undefined ? `${status.progress}%` : ""}</span>
                  </div>
                  <Progress value={status.progress} className="h-2 w-full" />
                </div>
              )}

              {status && status.status === "completed" && (
                <Alert className="bg-green-50 border-green-200 dark:bg-green-950/20 dark:border-green-900">
                  <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
                  <AlertDescription className="text-green-800 dark:text-green-300">
                    Processing complete! Redirecting to results...
                  </AlertDescription>
                </Alert>
              )}

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={handleProcess} disabled={!file || processing}>
          {processing ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : status?.status === "completed" ? (
            <>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Complete
            </>
          ) : (
            "Process Audio"
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}

