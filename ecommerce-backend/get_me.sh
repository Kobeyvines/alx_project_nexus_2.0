#!/bin/bash

# Config
BASE_URL="http://localhost:8000"
USERNAME="florence"
PASSWORD="your_password_here"

# Step 1: Get access token
ACCESS_TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}" | jq -r .access)

# Step 2: Call /users/me/ with token
curl -X GET "$BASE_URL/api/users/me/" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
