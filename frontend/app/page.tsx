"use client"

import { useEffect, useState } from "react"
import { ProcessAudio } from "@/components/process-audio"
import { ConversationList } from "@/components/conversation-list"
import { SpeakerStats } from "@/components/speaker-stats"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { checkApiAvailability } from "@/lib/api"
import { AlertCircle, CheckCircle2 } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function Home() {
  const [apiConnected, setApiConnected] = useState<boolean | null>(null)

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const isAvailable = await checkApiAvailability()
        setApiConnected(isAvailable)
      } catch (error) {
        console.error("Failed to check API availability:", error)
        setApiConnected(false)
      }
    }

    checkConnection()
  }, [])

  return (
    <main className="flex min-h-screen flex-col p-6 md:p-12">
      <div className="w-full max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Speaker Identification System</h1>
          <p className="text-muted-foreground mt-2">
            Process conversation audio files, identify speakers, and manage your speaker database.
          </p>
          
          {apiConnected === false && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Connection Error</AlertTitle>
              <AlertDescription>
                Cannot connect to the backend API. Make sure the Flask server is running on port 5000.
              </AlertDescription>
            </Alert>
          )}
          
          {apiConnected === true && (
            <Alert variant="default" className="mt-4 bg-green-50 border-green-200">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertTitle className="text-green-600">Connected</AlertTitle>
              <AlertDescription>
                Successfully connected to the backend API at {process.env.NEXT_PUBLIC_API_URL || "/api"}
              </AlertDescription>
            </Alert>
          )}
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <ProcessAudio />
          </div>

          <div className="lg:col-span-2">
            <Tabs defaultValue="conversations" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="conversations">Conversations</TabsTrigger>
                <TabsTrigger value="speakers">Speaker Database</TabsTrigger>
              </TabsList>

              <TabsContent value="conversations" className="mt-4">
                <ConversationList />
              </TabsContent>

              <TabsContent value="speakers" className="mt-4">
                <SpeakerStats />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </main>
  )
}

