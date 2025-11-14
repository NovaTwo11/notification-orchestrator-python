pipeline {
    agent {
        // Usamos una imagen base de Python
        docker {
            image 'python:3.11-slim'
        }
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Install Dependencies') {
            steps {
                sh 'pip install --no-cache-dir -r requirements.txt'
            }
        }
        stage('Lint / Static Analysis') {
            // Opcional: Si tuvieras Flake8 o Black
            steps {
                echo 'Skipping linting...'
                // sh 'flake8 .' 
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    def appImage = docker.build("notification-orchestrator:${env.BUILD_NUMBER}")
                }
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}