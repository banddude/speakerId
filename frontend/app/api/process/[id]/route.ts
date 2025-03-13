import { type NextRequest, NextResponse } from "next/server"
import fs from "fs/promises"
import path from "path"

// This would be configured based on your setup
const PROCESSING_STATUS_DIR = process.env.PROCESSING_STATUS_DIR || path.join(process.cwd(), "data", "processing")

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const id = params.id

    // Read the status file
    const statusFilePath = path.join(PROCESSING_STATUS_DIR, `${id}.json`)

    try {
      const content = await fs.readFile(statusFilePath, "utf-8")
      const status = JSON.parse(content)

      return NextResponse.json(status)
    } catch (err) {
      return NextResponse.json({ error: "Processing status not found" }, { status: 404 })
    }
  } catch (error) {
    console.error("Error getting processing status:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

