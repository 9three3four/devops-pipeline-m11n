#!/bin/bash
set -e

echo "🚀 Setting up complete DevOps environment..."

# Install additional tools
curl -sSL https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64 -o argocd
chmod +x argocd
sudo mv argocd /usr/local/bin/argocd

# Install Jenkins CLI
curl -L https://github.com/jenkinsci/jenkins/releases/download/jenkins-2.414.1/jenkins.war -o /tmp/jenkins.war
echo "alias jenkins='java -jar /tmp/jenkins.war'" >> ~/.bashrc

# Install Terraform
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Setup aliases
echo "alias k='kubectl'" >> ~/.bashrc
echo "alias mk='minikube'" >> ~/.bashrc

# Create project directories
mkdir -p ~/workspace/{services,infrastructure,scripts}

echo "✅ DevOps environment setup complete!"
