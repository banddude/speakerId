import { type NextRequest, NextResponse } from "next/server"
import { exec } from "child_process"
import { promisify } from "util"

const execAsync = promisify(exec)

export async function POST(request: NextRequest) {
  try {
    const { originalName, newName, updateAllInstances } = await request.json()

    if (!originalName || !newName) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 })
    }

    // Execute the Python script
    const { stdout, stderr } = await execAsync(
      `python rename_speaker.py "${originalName}" "${newName}" ${updateAllInstances ? "--update-all" : ""}`,
    )

    if (stderr) {
      console.error("Error executing Python script:", stderr)
      return NextResponse.json({ error: "Failed to rename speaker" }, { status: 500 })
    }

    // Parse the output from the Python script
    // This assumes your script outputs JSON
    const result = JSON.parse(stdout)

    return NextResponse.json(result)
  } catch (error) {
    console.error("Error renaming speaker:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

