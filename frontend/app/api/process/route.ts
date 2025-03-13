import { type NextRequest, NextResponse } from "next/server"
import { exec } from "child_process"
import { promisify } from "util"
import fs from "fs"
import path from "path"
import { v4 as uuidv4 } from "uuid"

const execAsync = promisify(exec)

// This would be configured based on your setup
const UPLOADS_DIR = process.env.UPLOADS_DIR || path.join(process.cwd(), "data", "uploads")
const PROCESSING_STATUS_DIR = process.env.PROCESSING_STATUS_DIR || path.join(process.cwd(), "data", "processing")

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }

    // Create directories if they don't exist
    if (!fs.existsSync(UPLOADS_DIR)) {
      fs.mkdirSync(UPLOADS_DIR, { recursive: true })
    }

    if (!fs.existsSync(PROCESSING_STATUS_DIR)) {
      fs.mkdirSync(PROCESSING_STATUS_DIR, { recursive: true })
    }

    // Generate unique ID for this processing job
    const processingId = uuidv4()
    const filename = file.name
    const filePath = path.join(UPLOADS_DIR, `${processingId}_${filename}`)

    // Write the file to disk
    const buffer = Buffer.from(await file.arrayBuffer())
    fs.writeFileSync(filePath, buffer)

    // Create initial status file
    const initialStatus = {
      id: processingId,
      filename,
      status: "queued",
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
    }

    const statusFilePath = path.join(PROCESSING_STATUS_DIR, `${processingId}.json`)
    fs.writeFileSync(
      statusFilePath,
      JSON.stringify(initialStatus, null, 2),
    )(
      // Start processing in the background
      // This would typically be handled by a job queue in production
      async () => {
        try {
          // Update status to processing
          const processingStatus = {
            ...initialStatus,
            status: "processing",
            stage: "Transcribing audio",
            progress: 0,
            updated: new Date().toISOString(),
          }
          fs.writeFileSync(statusFilePath, JSON.stringify(processingStatus, null, 2))

          // Execute the Python script
          const { stdout, stderr } = await execAsync(`python identify_conversation.py "${filePath}"`)

          if (stderr) {
            console.error("Error executing Python script:", stderr)

            // Update status to failed
            const failedStatus = {
              ...processingStatus,
              status: "failed",
              error: "Failed to process audio",
              updated: new Date().toISOString(),
            }
            fs.writeFileSync(statusFilePath, JSON.stringify(failedStatus, null, 2))
            return
          }

          // Parse the output from the Python script
          // This assumes your script outputs JSON
          const result = JSON.parse(stdout)

          // Update status to completed
          const completedStatus = {
            ...processingStatus,
            status: "completed",
            progress: 100,
            result,
            updated: new Date().toISOString(),
          }
          fs.writeFileSync(statusFilePath, JSON.stringify(completedStatus, null, 2))

          // Clean up the temporary file
          // fs.unlinkSync(filePath)
        } catch (error) {
          console.error("Error processing audio:", error)

          // Update status to failed
          const failedStatus = {
            ...initialStatus,
            status: "failed",
            error: error instanceof Error ? error.message : "Unknown error",
            updated: new Date().toISOString(),
          }
          fs.writeFileSync(statusFilePath, JSON.stringify(failedStatus, null, 2))
        }
      },
    )()

    return NextResponse.json(initialStatus)
  } catch (error) {
    console.error("Error processing audio:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

