#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}       LTI AI Tutor - Easy Installer             ${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check for Docker Compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo -e "${YELLOW}Error: Docker Compose is not installed or not found.${NC}"
    exit 1
fi

echo -e "\n${GREEN}[1/5] Configuring Environment${NC}"
read -p "Enter your domain name (or press Enter for localhost): " DOMAIN_NAME
DOMAIN_NAME=${DOMAIN_NAME:-localhost}

read -p "Enter the port to run the application on (default: 8080): " APP_PORT
APP_PORT=${APP_PORT:-8080}

if [ "$DOMAIN_NAME" = "localhost" ]; then
    if [ "$APP_PORT" = "80" ]; then
        TOOL_URL="http://localhost"
    else
        TOOL_URL="http://localhost:$APP_PORT"
    fi
else
    # Assume HTTPS for domains unless specified otherwise, standard port 443 hidden
    if [ "$APP_PORT" = "443" ]; then
         TOOL_URL="https://$DOMAIN_NAME"
    elif [ "$APP_PORT" = "80" ]; then
         TOOL_URL="http://$DOMAIN_NAME"
    else
         TOOL_URL="http://$DOMAIN_NAME:$APP_PORT"
    fi
fi

echo -e "Using Tool URL: ${BLUE}$TOOL_URL${NC}"

# Generate Keys
echo -e "\n${GREEN}[2/5] Generating Security Keys${NC}"
mkdir -p backend/keys
if [ ! -f backend/keys/private.pem ]; then
    # Create a temporary python script to run key generation
    echo "Generating RSA keys..."
    cd backend
    # Keys should be in backend/keys, so relative to backend it is "keys"
    KEY_DIR=keys python3 scripts/generate_keys.py
    cd ..
else
    echo "Keys already exist. Skipping generation."
fi

# Display Config for Open edX
echo -e "\n${GREEN}[3/5] Open edX Configuration${NC}"
echo -e "Please go to your Open edX Admin > LTI Configuration and add a new tool with:"
echo -e "------------------------------------------------"
echo -e "Tool URL:             ${YELLOW}$TOOL_URL/lti/launch${NC}"
echo -e "OIDC Login URL:       ${YELLOW}$TOOL_URL/lti/login${NC}"
echo -e "Public Keys URL (JWKS): ${YELLOW}$TOOL_URL/lti/jwks${NC}"
echo -e "Redirect URI(s):      ${YELLOW}$TOOL_URL/lti/launch${NC}  <-- IMPORTANTE"
echo -e "------------------------------------------------"

echo -e "\n${YELLOW}Waiting for you to configure Open edX...${NC}"
echo -e "To find the issuer: It is usually the URL of your LMS (e.g., http://local.openedx.io)"
read -p "Enter the LTI Issuer: " LTI_ISSUER
read -p "Enter the Client ID provided by Open edX: " LTI_CLIENT_ID
read -p "Enter the Deployment ID (default: 1): " LTI_DEPLOYMENT_ID
LTI_DEPLOYMENT_ID=${LTI_DEPLOYMENT_ID:-1}

echo -e "\n${YELLOW}Step 3.1: Platform Endpoints (Copy from Open edX)${NC}"
echo -e "Open edX provides specific URLs for the connection (Keyset, Access Token, Login URL)."
read -p "Enter the Platform OIDC Login URL (initiation url): " LTI_AUTH_URL
read -p "Enter the Platform Access Token URL: " LTI_TOKEN_URL
read -p "Enter the Platform Keyset URL (JWKS): " LTI_JWKS_URL

# Create .env file
echo -e "\n${GREEN}[4/5] Saving Configuration${NC}"
cat > backend/.env << EOL
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
PORT=5000

# Gemini AI
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash

# LLM Configuration
LLM_PROVIDER=gemini
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=gemma:2b

# LTI Configuration
LTI_ISSUER=$LTI_ISSUER
LTI_CLIENT_ID=$LTI_CLIENT_ID
LTI_DEPLOYMENT_ID=$LTI_DEPLOYMENT_ID
LTI_AUTH_URL=$LTI_AUTH_URL
LTI_TOKEN_URL=$LTI_TOKEN_URL
LTI_JWKS_URL=$LTI_JWKS_URL
LTI_TOOL_URL=$TOOL_URL

# Keys
LTI_PRIVATE_KEY_PATH=/app/keys/private.pem
LTI_PUBLIC_KEY_PATH=/app/keys/public.pem

# Frontend
FRONTEND_URL=$TOOL_URL
APP_PORT=$APP_PORT
EOL

echo -e "Configuration saved to backend/.env"
echo -e "${YELLOW}IMPORTANT: Please edit backend/.env and add your GEMINI_API_KEY manually.${NC}"

# Build and Run
echo -e "\n${GREEN}[5/5] Launching Application${NC}"
read -p "Do you want to start the application now? (y/n): " START_APP
if [[ "$START_APP" =~ ^[Yy]$ ]]; then
    echo "Starting Docker containers..."
    $DOCKER_COMPOSE_CMD up -d --build
    echo -e "\n${GREEN}Application is running!${NC}"
    echo -e "Frontend: $TOOL_URL"
    echo -e "Backend:  $TOOL_URL/api"
else
    echo -e "\nYou can start the application later by running: ${BLUE}$DOCKER_COMPOSE_CMD up -d${NC}"
fi
