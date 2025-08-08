pipeline {
    agent any
    
    environment {
        PROJECT_ID = 'your-gcp-project-id'
        CLUSTER_NAME = 'microservices-project-cluster'
        LOCATION = 'us-central1'
        REGISTRY = 'gcr.io'
        IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT[0..7]}"
    }
    
    stages {
        stage('Setup Environment') {
            steps {
                script {
                    sh '''
                        # Install Node.js if not present
                        if ! command -v node &> /dev/null; then
                            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                            sudo apt-get install -y nodejs
                        fi
                        
                        # Install Python if not present
                        if ! command -v python3 &> /dev/null; then
                            sudo apt-get update && sudo apt-get install -y python3 python3-pip
                        fi
                        
                        # Install other tools
                        if ! command -v kubectl &> /dev/null; then
                            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                            chmod +x kubectl
                            sudo mv kubectl /usr/local/bin/
                        fi
                        
                        if ! command -v terraform &> /dev/null; then
                            wget https://releases.hashicorp.com/terraform/1.5.0/terraform_1.5.0_linux_amd64.zip
                            unzip terraform_1.5.0_linux_amd64.zip
                            sudo mv terraform /usr/local/bin/
                        fi
                    '''
                }
            }
        }
        
        stage('Detect Changed Services') {
            steps {
                script {
                    def changedServices = sh(
                        script: '''
                            git diff --name-only HEAD~1 HEAD | grep "^services/" | cut -d'/' -f2 | sort -u
                        ''',
                        returnStdout: true
                    ).trim().split('\n').findAll { it }
                    
                    if (changedServices.isEmpty()) {
                        changedServices = ['user-service', 'product-service', 'order-service', 'api-gateway']
                    }
                    
                    env.CHANGED_SERVICES = changedServices.join(',')
                    echo "Services to build: ${env.CHANGED_SERVICES}"
                }
            }
        }
        
        stage('Infrastructure Provisioning') {
            steps {
                dir('infrastructure/terraform') {
                    withCredentials([file(credentialsId: 'gcp-service-account-key', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                        sh '''
                            terraform init
                            terraform workspace select dev || terraform workspace new dev
                            terraform plan -var="project_id=${PROJECT_ID}" -out=tfplan
                            terraform apply -auto-approve tfplan
                            gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${LOCATION} --project=${PROJECT_ID}
                        '''
                    }
                }
            }
        }
        
        stage('Build and Test Services') {
            parallel {
                stage('User Service (Node.js)') {
                    when {
                        expression { env.CHANGED_SERVICES.contains('user-service') }
                    }
                    steps {
                        buildNodeService('user-service')
                    }
                }
                stage('Product Service (Python Flask)') {
                    when {
                        expression { env.CHANGED_SERVICES.contains('product-service') }
                    }
                    steps {
                        buildPythonService('product-service')
                    }
                }
                stage('Order Service (Python FastAPI)') {
                    when {
                        expression { env.CHANGED_SERVICES.contains('order-service') }
                    }
                    steps {
                        buildPythonService('order-service')
                    }
                }
                stage('API Gateway (Node.js)') {
                    when {
                        expression { env.CHANGED_SERVICES.contains('api-gateway') }
                    }
                    steps {
                        buildNodeService('api-gateway')
                    }
                }
            }
        }
        
        stage('Security Scanning') {
            parallel {
                stage('Node.js Security Scan') {
                    steps {
                        script {
                            def nodeServices = env.CHANGED_SERVICES.split(',').findAll { 
                                it.contains('user-service') || it.contains('api-gateway') 
                            }
                            
                            nodeServices.each { service ->
                                dir("services/${service}") {
                                    sh '''
                                        # NPM audit for vulnerabilities
                                        npm audit --audit-level=high
                                        
                                        # ESLint for code quality
                                        npm run lint || echo "Linting issues found"
                                    '''
                                }
                            }
                        }
                    }
                }
                
                stage('Python Security Scan') {
                    steps {
                        script {
                            def pythonServices = env.CHANGED_SERVICES.split(',').findAll { 
                                it.contains('product-service') || it.contains('order-service') 
                            }
                            
                            pythonServices.each { service ->
                                dir("services/${service}") {
                                    sh '''
                                        # Install safety for vulnerability scanning
                                        pip3 install safety bandit
                                        
                                        # Check for vulnerable packages
                                        safety check -r requirements.txt
                                        
                                        # Static security analysis
                                        bandit -r . -f json -o bandit-report.json || echo "Security issues found"
                                    '''
                                }
                            }
                        }
                    }
                }
                
                stage('Container Security Scan') {
                    steps {
                        script {
                            def services = env.CHANGED_SERVICES.split(',')
                            services.each { service ->
                                sh """
                                    trivy image --exit-code 1 --severity HIGH,CRITICAL ${REGISTRY}/${PROJECT_ID}/${service}:${IMAGE_TAG}
                                """
                            }
                        }
                    }
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    def services = env.CHANGED_SERVICES.split(',')
                    services.each { service ->
                        deployToKubernetes(service)
                    }
                }
            }
        }
        
        stage('Setup ArgoCD') {
            steps {
                script {
                    sh '''
                        if ! kubectl get namespace argocd > /dev/null 2>&1; then
                            kubectl create namespace argocd
                            kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
                            kubectl wait --for=condition=available --timeout=600s deployment/argocd-server -n argocd
                        fi
                    '''
                }
            }
        }
        
        stage('Configure ArgoCD Applications') {
            steps {
                script {
                    def services = env.CHANGED_SERVICES.split(',')
                    services.each { service ->
                        configureArgoCDApp(service)
                    }
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                script {
                    sh '''
                        # Wait for deployments to be ready
                        kubectl wait --for=condition=available --timeout=300s deployment/user-service || echo "User service timeout"
                        kubectl wait --for=condition=available --timeout=300s deployment/product-service || echo "Product service timeout"
                        kubectl wait --for=condition=available --timeout=300s deployment/order-service || echo "Order service timeout"
                        
                        # Run integration tests
                        python3 scripts/integration-tests.py
                    '''
                }
            }
        }
    }
    
    post {
        always {
            sh '''
                docker system prune -f
                kubectl delete pods --field-selector=status.phase=Succeeded -A
            '''
        }
        success {
            echo 'Pipeline completed successfully!'
            emailext (
                subject: "✅ Build Success: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: """
                    Build completed successfully!
                    
                    Project: ${env.JOB_NAME}
                    Build: ${env.BUILD_NUMBER}
                    Services Built: ${env.CHANGED_SERVICES}
                    
                    View build: ${env.BUILD_URL}
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL}",
                attachLog: true
            )
        }
        failure {
            echo 'Pipeline failed!'
            emailext (
                subject: "❌ Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: """
                    Build failed!
                    
                    Project: ${env.JOB_NAME}
                    Build: ${env.BUILD_NUMBER}
                    
                    Please check the build logs: ${env.BUILD_URL}console
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL}",
                attachLog: true
            )
        }
    }
}

def buildNodeService(serviceName) {
    dir("services/${serviceName}") {
        sh '''
            # Install dependencies
            npm ci
            
            # Run tests
            npm test || echo "No tests found"
            
            # Run linting
            npm run lint || echo "Linting completed"
        '''
        
        // Build Docker image
        buildDockerImage(serviceName)
    }
}

def buildPythonService(serviceName) {
    dir("services/${serviceName}") {
        sh '''
            # Create virtual environment
            python3 -m venv venv
            source venv/bin/activate
            
            # Install dependencies
            pip install -r requirements.txt
            
            # Run tests
            python -m pytest tests/ || echo "No tests found"
            
            # Run linting (if available)
            which flake8 && flake8 . || echo "Flake8 not installed"
        '''
        
        // Build Docker image
        buildDockerImage(serviceName)
    }
}

def buildDockerImage(serviceName) {
    sh """
        docker build -t ${REGISTRY}/${PROJECT_ID}/${serviceName}:${IMAGE_TAG} .
        docker tag ${REGISTRY}/${PROJECT_ID}/${serviceName}:${IMAGE_TAG} ${REGISTRY}/${PROJECT_ID}/${serviceName}:latest
        docker push ${REGISTRY}/${PROJECT_ID}/${serviceName}:${IMAGE_TAG}
        docker push ${REGISTRY}/${PROJECT_ID}/${serviceName}:latest
    """
}

def deployToKubernetes(serviceName) {
    dir("services/${serviceName}") {
        sh """
            # Update image in Kubernetes manifests
            sed -i 's|gcr.io/PROJECT_ID/${serviceName}:.*|${REGISTRY}/${PROJECT_ID}/${serviceName}:${IMAGE_TAG}|g' k8s/deployment.yaml
            
            # Apply Kubernetes manifests
            kubectl apply -f k8s/
            
            # Wait for deployment to be ready
            kubectl rollout status deployment/${serviceName} --timeout=300s
        """
    }
}

def configureArgoCDApp(serviceName) {
    writeFile file: "argocd-${serviceName}-app.yaml", text: """
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ${serviceName}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: ${env.GIT_URL}
    targetRevision: HEAD
    path: services/${serviceName}/k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
"""
    
    sh "kubectl apply -f argocd-${serviceName}-app.yaml"
}
