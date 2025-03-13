import { type NextRequest, NextResponse } from "next/server"
import { exec } from "child_process"
import { promisify } from "util"
import fs from "fs"
import path from "path"
import { v4 as uuidv4 } from "uuid"

const execAsync = promisify(exec)

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get("file") as File

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }

    // Create a temporary directory for processing
    const tempDir = path.join(process.cwd(), "tmp")
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true })
    }

    // Generate unique filename
    const fileId = uuidv4()
    const filePath = path.join(tempDir, `${fileId}_${file.name}`)

    // Write the file to disk
    const buffer = Buffer.from(await file.arrayBuffer())
    fs.writeFileSync(filePath, buffer)

    // Execute the Python script
    const { stdout, stderr } = await execAsync(`python identify_conversation.py "${filePath}"`)

    if (stderr) {
      console.error("Error executing Python script:", stderr)
      return NextResponse.json({ error: "Failed to process audio" }, { status: 500 })
    }

    // Parse the output from the Python script
    // This assumes your script outputs JSON
    const result = JSON.parse(stdout)

    // Clean up the temporary file
    fs.unlinkSync(filePath)

    return NextResponse.json(result)
  } catch (error) {
    console.error("Error processing audio:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

