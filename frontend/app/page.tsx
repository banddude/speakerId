import { ProcessAudio } from "@/components/process-audio"
import { ConversationList } from "@/components/conversation-list"
import { SpeakerStats } from "@/components/speaker-stats"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col p-6 md:p-12">
      <div className="w-full max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Speaker Identification System</h1>
          <p className="text-muted-foreground mt-2">
            Process conversation audio files, identify speakers, and manage your speaker database.
          </p>
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

