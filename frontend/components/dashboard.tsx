"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { RecentUploads } from "@/components/recent-uploads"
import { SpeakerManagement } from "@/components/speaker-management"

export function Dashboard() {
  const [activeTab, setActiveTab] = useState("recent")

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dashboard</CardTitle>
        <CardDescription>Manage your transcriptions and speakers</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="recent" onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="recent">Recent Uploads</TabsTrigger>
            <TabsTrigger value="speakers">Speaker Management</TabsTrigger>
          </TabsList>
          <TabsContent value="recent" className="mt-4">
            <RecentUploads />
          </TabsContent>
          <TabsContent value="speakers" className="mt-4">
            <SpeakerManagement />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

