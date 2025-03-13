import { type NextRequest, NextResponse } from "next/server"
import fs from "fs"
import path from "path"

// This would be configured based on your setup
const UPLOADS_DIR = process.env.UPLOADS_DIR || path.join(process.cwd(), "data", "uploads")

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const id = params.id

    // Find the audio file with this ID prefix
    const files = fs.readdirSync(UPLOADS_DIR)
    const audioFile = files.find((file) => file.startsWith(id))

    if (!audioFile) {
      return new NextResponse("Audio file not found", { status: 404 })
    }

    const filePath = path.join(UPLOADS_DIR, audioFile)
    const fileStats = fs.statSync(filePath)

    // Determine content type based on file extension
    const ext = path.extname(audioFile).toLowerCase()
    let contentType = "audio/mpeg"

    if (ext === ".wav") {
      contentType = "audio/wav"
    } else if (ext === ".m4a") {
      contentType = "audio/m4a"
    } else if (ext === ".ogg") {
      contentType = "audio/ogg"
    }

    // Stream the file
    const fileStream = fs.createReadStream(filePath)

    return new NextResponse(fileStream as any, {
      headers: {
        "Content-Type": contentType,
        "Content-Length": fileStats.size.toString(),
        "Accept-Ranges": "bytes",
      },
    })
  } catch (error) {
    console.error("Error streaming audio:", error)
    return new NextResponse("Internal server error", { status: 500 })
  }
}

