#!/bin/bash
# Script to restart Datasette with performance optimizations
echo "Current directory: $(pwd)"
# Print directory contents
echo "Directory contents:"
ls -la

# Stop any existing container
docker rm -f datasette_web 2>/dev/null

# Build the optimized container
cd /opt/datasette
docker build -t oksiks/kmr-voting-explorer:latest .

# Run with performance optimizations
docker run -d --name datasette_web -p 80:8001 \
  -v /opt/datasette/kmr_voting_data.db:/data/kmr_voting_data.db \
  -v /opt/datasette/metadata.json:/data/metadata.json \
  --memory=1g --cpus=1 \
  oksiks/kmr-voting-explorer:latest 

# Check container status
echo "Container status:"
docker ps -a | grep datasette_web


# Check container logs
echo "Container logs:"
docker logs datasette_web

echo "Script completed"


# docker run -d --name datasette_web -p 80:8001 \
#   -v /opt/datasette/kmr_voting_data.db:/data/kmr_voting_data.db \
#   -v /opt/datasette/metadata.json:/data/metadata.json \
#   --memory=1g --cpus=1 \
#   oksiks/kmr-voting-explorer:latest

echo "Optimized Datasette container started!"
echo "Visit http://142.93.109.39/ to access your site."
