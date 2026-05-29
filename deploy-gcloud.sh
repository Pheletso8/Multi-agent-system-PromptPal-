#!/bin/bash
# ============================================================
# deploy-gcloud.sh — Deploy PromptPal to Google Cloud Run
# ============================================================
# Usage:
#   chmod +x deploy-gcloud.sh
#   ./deploy-gcloud.sh YOUR_PROJECT_ID YOUR_GROQ_API_KEY
#
# Prerequisites:
#   1. Google Cloud CLI installed (https://cloud.google.com/sdk/docs/install)
#   2. Logged in: gcloud auth login
#   3. Billing enabled on your GCP project
# ============================================================

set -e  # Exit on any error

PROJECT_ID="${1:?Usage: ./deploy-gcloud.sh PROJECT_ID GROQ_API_KEY}"
GROQ_API_KEY="${2:?Usage: ./deploy-gcloud.sh PROJECT_ID GROQ_API_KEY}"
REGION="us-central1"

echo "============================================"
echo " PromptPal — Google Cloud Run Deployment"
echo " Project:  $PROJECT_ID"
echo " Region:   $REGION"
echo "============================================"

# --- 0. Set project ---
gcloud config set project "$PROJECT_ID"

# --- 1. Enable required APIs ---
echo ""
echo ">>> Enabling Cloud Run & Container Registry APIs..."
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# --- 2. Build & Deploy SCHOLAR ---
echo ""
echo ">>> Building & deploying Scholar agent..."
gcloud builds submit ./agents/scholar \
  --tag "gcr.io/$PROJECT_ID/promptpal-scholar"

gcloud run deploy promptpal-scholar \
  --image "gcr.io/$PROJECT_ID/promptpal-scholar" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GROQ_API_KEY=$GROQ_API_KEY"

SCHOLAR_URL=$(gcloud run services describe promptpal-scholar \
  --region "$REGION" --format "value(status.url)")
echo "Scholar deployed at: $SCHOLAR_URL"

# --- 3. Build & Deploy COACH ---
echo ""
echo ">>> Building & deploying Coach agent..."
gcloud builds submit ./agents/coach \
  --tag "gcr.io/$PROJECT_ID/promptpal-coach"

gcloud run deploy promptpal-coach \
  --image "gcr.io/$PROJECT_ID/promptpal-coach" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GROQ_API_KEY=$GROQ_API_KEY"

COACH_URL=$(gcloud run services describe promptpal-coach \
  --region "$REGION" --format "value(status.url)")
echo "Coach deployed at: $COACH_URL"

# --- 4. Build & Deploy FORMATTER ---
echo ""
echo ">>> Building & deploying Formatter agent..."
gcloud builds submit ./agents/formatter \
  --tag "gcr.io/$PROJECT_ID/promptpal-formatter"

gcloud run deploy promptpal-formatter \
  --image "gcr.io/$PROJECT_ID/promptpal-formatter" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated

FORMATTER_URL=$(gcloud run services describe promptpal-formatter \
  --region "$REGION" --format "value(status.url)")
echo "Formatter deployed at: $FORMATTER_URL"

# --- 5. Build & Deploy API GATEWAY ---
echo ""
echo ">>> Building & deploying API Gateway..."
gcloud builds submit . \
  --tag "gcr.io/$PROJECT_ID/promptpal-api"

gcloud run deploy promptpal-api \
  --image "gcr.io/$PROJECT_ID/promptpal-api" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "SCHOLAR_URL=${SCHOLAR_URL}/solve,COACH_URL=${COACH_URL}/process,FORMATTER_URL=${FORMATTER_URL}/format"

API_URL=$(gcloud run services describe promptpal-api \
  --region "$REGION" --format "value(status.url)")

echo ""
echo "============================================"
echo " ✅ DEPLOYMENT COMPLETE!"
echo "============================================"
echo " API Gateway:  $API_URL"
echo " Scholar:      $SCHOLAR_URL"
echo " Coach:        $COACH_URL"
echo " Formatter:    $FORMATTER_URL"
echo ""
echo " Test it:"
echo "   curl -X POST $API_URL/ask \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"question\": \"What is 7 + 7?\"}'"
echo ""
echo " Update your Vercel frontend to use:"
echo "   $API_URL/ask"
echo "============================================"
