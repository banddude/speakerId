import { type NextRequest, NextResponse } from "next/server"
import fs from "fs/promises"
import path from "path"

// This would be configured based on your setup
const CONVERSATIONS_DIR = process.env.CONVERSATIONS_DIR || path.join(process.cwd(), "data", "conversations")

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const id = params.id

    // Read the conversation file
    const filePath = path.join(CONVERSATIONS_DIR, `${id}.json`)

    try {
      const content = await fs.readFile(filePath, "utf-8")
      const conversation = JSON.parse(content)

      return NextResponse.json(conversation)
    } catch (err) {
      return NextResponse.json({ error: "Conversation not found" }, { status: 404 })
    }
  } catch (error) {
    console.error("Error getting conversation:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

