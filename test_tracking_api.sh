#!/bin/bash
# Script to test tracking API endpoints with curl

# Configuration
API_BASE="http://localhost:5050"
API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJtaWd1ZWw2OTZtZ0BnbWFpbC5jb20iLCJuYW1lIjoiTWlndWVsIEdvbnpcdTAwZTFsZXoiLCJleHAiOjE3NDc0MzY1NDcsImlhdCI6MTc0NDg0NDU0NywidHlwZSI6ImFjY2VzcyJ9.eKvxnLqe49hLBuiU6DzWYI00G5i3v7sQwRwe0GgKBCU"
TODAY=$(date +%Y-%m-%d)

echo "=== Testing Nutrition Tracking API ==="
echo "Using date: $TODAY"
echo ""

# 1. Test if the nutrition calculate-macros endpoint works (already confirmed)
echo "1. Testing /api/nutrition/calculate-macros endpoint (reference test):"
curl -s -X POST "$API_BASE/api/nutrition/calculate-macros" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "units": "metric",
    "formula": "mifflin_st_jeor",
    "gender": "male",
    "age": 35,
    "height": 180,
    "weight": 80,
    "body_fat_percentage": 15,
    "activity_level": "moderate",
    "goal": "lose",
    "goal_intensity": "normal"
  }' | jq
echo ""

# 2. Test GET tracking for today (should return null or existing data)
echo "2. Testing GET /api/nutrition/tracking/day/$TODAY endpoint:"
curl -s -X GET "$API_BASE/api/nutrition/tracking/day/$TODAY" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" | jq
echo ""

# 3. Test saving tracking data
echo "3. Testing POST /api/nutrition/tracking endpoint:"
curl -s -X POST "$API_BASE/api/nutrition/tracking" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_date": "'$TODAY'",
    "completed_meals": {
      "Desayuno": true,
      "Almuerzo": false,
      "Comida": true,
      "Merienda": false,
      "Cena": false
    },
    "calorie_note": "Test from curl script",
    "actual_calories": 1800,
    "excess_deficit": -200
  }' | jq
echo ""

# 4. Test GET tracking for today again (should now return data)
echo "4. Testing GET /api/nutrition/tracking/day/$TODAY after save:"
curl -s -X GET "$API_BASE/api/nutrition/tracking/day/$TODAY" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" | jq
echo ""

# 5. Test getting weekly tracking
echo "5. Testing GET /api/nutrition/tracking/week endpoint:"
curl -s -X GET "$API_BASE/api/nutrition/tracking/week" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" | jq
echo ""

# 6. Test getting weekly summary
echo "6. Testing GET /api/nutrition/tracking/summary endpoint:"
curl -s -X GET "$API_BASE/api/nutrition/tracking/summary" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" | jq
echo ""

echo "Tests completed."