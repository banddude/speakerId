"use client"

import type React from "react"

import { useState } from "react"
import { UploadIcon, FileAudio, Loader2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

export function Upload() {
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setProgress(0)

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) {
          clearInterval(interval)
          return prev
        }
        return prev + 5
      })
    }, 300)

    try {
      // Here you would implement the actual file upload to your backend
      // const formData = new FormData()
      // formData.append('file', file)
      // const response = await fetch('/api/upload', { method: 'POST', body: formData })

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 3000))

      setProgress(100)
      setTimeout(() => {
        setIsUploading(false)
        setFile(null)
        setProgress(0)
      }, 500)
    } catch (error) {
      console.error("Upload failed:", error)
      setIsUploading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Conversation</CardTitle>
        <CardDescription>Upload an audio file to transcribe and identify speakers</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center space-y-4">
          {!file ? (
            <div className="flex flex-col items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg p-12 w-full">
              <UploadIcon className="h-12 w-12 text-muted-foreground mb-4" />
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
              {isUploading && (
                <div className="space-y-2">
                  <Progress value={progress} className="h-2 w-full" />
                  <p className="text-xs text-right text-muted-foreground">{progress}%</p>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={handleUpload} disabled={!file || isUploading}>
          {isUploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            "Upload and Process"
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}

