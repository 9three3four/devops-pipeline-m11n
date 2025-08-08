#!/bin/bash
set -e

echo "🔄 Starting services..."

# Start Docker daemon
sudo service docker start

# Start Minikube
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=20g \
  --driver=docker \
  --embed-certs

# Enable minikube addons
minikube addons enable dashboard
minikube addons enable metrics-server

# Wait for cluster to be ready
kubectl wait --for=condition=Ready nodes --all --timeout=300s

echo "✅ Minikube cluster is ready!"
echo "🌐 Minikube IP: $(minikube ip)"
