import { NextResponse } from "next/server"
import { exec } from "child_process"
import { promisify } from "util"

const execAsync = promisify(exec)

export async function GET() {
  try {
    // Execute the Python script to get all speakers
    const { stdout, stderr } = await execAsync("python manage_voice_db.py --list-all")

    if (stderr) {
      console.error("Error executing Python script:", stderr)
      return NextResponse.json({ error: "Failed to get speakers" }, { status: 500 })
    }

    // Parse the output from the Python script
    // This assumes your script outputs JSON
    const speakers = JSON.parse(stdout)

    return NextResponse.json(speakers)
  } catch (error) {
    console.error("Error getting speakers:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

