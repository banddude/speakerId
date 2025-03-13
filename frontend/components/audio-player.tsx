"use client"

import { useState, useEffect, useRef } from "react"
import { Play, Pause, Volume2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"

interface AudioPlayerProps {
  audioUrl: string
  startTime?: number
  endTime?: number
  onPlayStateChange?: (isPlaying: boolean) => void
  small?: boolean
}

export function AudioPlayer({ audioUrl, startTime = 0, endTime, onPlayStateChange, small = false }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const updateTime = () => {
      setCurrentTime(audio.currentTime)

      // If we've reached the end time, pause the audio
      if (endTime && audio.currentTime >= endTime) {
        audio.pause()
        audio.currentTime = startTime
        setIsPlaying(false)
        if (onPlayStateChange) onPlayStateChange(false)
      }
    }

    const handlePlay = () => {
      setIsPlaying(true)
      if (onPlayStateChange) onPlayStateChange(true)
    }

    const handlePause = () => {
      setIsPlaying(false)
      if (onPlayStateChange) onPlayStateChange(false)
    }

    const handleLoadedMetadata = () => {
      setDuration(audio.duration)
    }

    audio.addEventListener("timeupdate", updateTime)
    audio.addEventListener("play", handlePlay)
    audio.addEventListener("pause", handlePause)
    audio.addEventListener("loadedmetadata", handleLoadedMetadata)

    return () => {
      audio.removeEventListener("timeupdate", updateTime)
      audio.removeEventListener("play", handlePlay)
      audio.removeEventListener("pause", handlePause)
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata)
    }
  }, [endTime, startTime, onPlayStateChange])

  // Set the start time when it changes
  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    if (!isPlaying) {
      audio.currentTime = startTime
    }
  }, [startTime, isPlaying])

  const togglePlayback = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
    } else {
      // If we're at the end, reset to start time
      if (endTime && audio.currentTime >= endTime) {
        audio.currentTime = startTime
      } else if (audio.currentTime < startTime || (endTime && audio.currentTime > endTime)) {
        audio.currentTime = startTime
      }

      audio.play()
    }
  }

  const handleTimeChange = (value: number[]) => {
    const audio = audioRef.current
    if (!audio) return

    const newTime = value[0]
    audio.currentTime = newTime
    setCurrentTime(newTime)
  }

  const handleVolumeChange = (value: number[]) => {
    const audio = audioRef.current
    if (!audio) return

    const newVolume = value[0]
    audio.volume = newVolume
    setVolume(newVolume)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  // For segment playback, we show a simplified UI
  if (small) {
    return (
      <div className="inline-flex items-center">
        <audio ref={audioRef} src={audioUrl} preload="metadata" className="hidden" />
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={togglePlayback}>
          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <audio ref={audioRef} src={audioUrl} preload="metadata" className="hidden" />

      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{formatTime(currentTime)}</span>
        <div className="flex items-center gap-2">
          <Volume2 className="h-4 w-4 text-muted-foreground" />
          <Slider value={[volume]} max={1} step={0.01} onValueChange={handleVolumeChange} className="w-24" />
        </div>
        <span className="text-sm text-muted-foreground">{endTime ? formatTime(endTime) : formatTime(duration)}</span>
      </div>

      <Slider
        value={[currentTime]}
        min={startTime}
        max={endTime || duration}
        step={0.1}
        onValueChange={handleTimeChange}
        className="cursor-pointer"
      />

      <div className="flex justify-center">
        <Button onClick={togglePlayback} size="sm">
          {isPlaying ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
          {isPlaying ? "Pause" : "Play"}
        </Button>
      </div>
    </div>
  )
}

