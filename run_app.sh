#!/bin/bash

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Start the backend server
echo "Starting Flask backend server..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait a moment for the backend to start
sleep 2

# Start the frontend server
echo "Starting Next.js frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Both servers are running!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:5000"
echo "Press Ctrl+C to stop both servers"

# Function to kill processes on exit
function cleanup {
    echo "Stopping servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT

# Keep the script running
while true; do
    sleep 1
done 