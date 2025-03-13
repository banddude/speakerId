import { NextResponse } from "next/server"
import { exec } from "child_process"
import { promisify } from "util"
import fs from "fs/promises"
import path from "path"

const execAsync = promisify(exec)

// This would be configured based on your setup
const CONVERSATIONS_DIR = process.env.CONVERSATIONS_DIR || path.join(process.cwd(), "data", "conversations")

export async function GET() {
  try {
    // Check if directory exists
    try {
      await fs.access(CONVERSATIONS_DIR)
    } catch (err) {
      // Create directory if it doesn't exist
      await fs.mkdir(CONVERSATIONS_DIR, { recursive: true })
      return NextResponse.json([])
    }

    // Read all conversation files
    const files = await fs.readdir(CONVERSATIONS_DIR)
    const jsonFiles = files.filter((file) => file.endsWith(".json"))

    // Read and parse each file
    const conversations = await Promise.all(
      jsonFiles.map(async (file) => {
        const content = await fs.readFile(path.join(CONVERSATIONS_DIR, file), "utf-8")
        return JSON.parse(content)
      }),
    )

    // Sort by created date (newest first)
    conversations.sort((a, b) => new Date(b.created).getTime() - new Date(a.created).getTime())

    return NextResponse.json(conversations)
  } catch (error) {
    console.error("Error getting conversations:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

