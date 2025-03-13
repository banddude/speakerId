#!/bin/bash

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Create the frontend .env.local file with the correct API URL
echo "Creating frontend environment configuration..."
echo "NEXT_PUBLIC_API_URL=http://localhost:5000/api" > frontend/.env.local
echo "Frontend environment configured to connect to backend at http://localhost:5000/api"

# Start the backend server
echo "Starting Flask backend server..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait a moment for the backend to start
echo "Waiting for backend to initialize..."
sleep 3

# Verify backend is running
if curl -s http://localhost:5000/api/conversations > /dev/null; then
    echo "✅ Backend API is accessible at http://localhost:5000/api"
else
    echo "⚠️ Backend API does not appear to be responding. Check for errors above."
fi

# Start the frontend server
echo "Starting Next.js frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "==================================================="
echo "🚀 Both servers are running!"
echo "📱 Frontend: http://localhost:3000"
echo "⚙️ Backend: http://localhost:5000"
echo "🔄 API connection: http://localhost:5000/api"
echo "==================================================="
echo ""
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