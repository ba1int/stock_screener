#!/bin/bash
# Setup script for the stock screener

# Create required directories
mkdir -p component_results
mkdir -p test_results
mkdir -p stock_screener/data/results

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from template. Please update with your API keys."
else
    echo ".env file already exists."
fi

# Install dependencies
pip install -r requirements.txt

echo "Setup complete!" 