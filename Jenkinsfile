// Jenkinsfile para notification-orchestrator-python

pipeline {
    // Usamos 'agent any' por la misma razón: acceso al socket de Docker
    agent any 

    environment {
        // Nombre de la imagen que construiremos
        IMAGE_NAME = 'notification-orchestrator'
        
        // Tag (usamos el número de build de Jenkins)
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        
        // Contenedor de Python para usar en la etapa de pruebas/linting
        PYTHON_IMAGE = 'python:3.11-slim'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm // Clona tu código
            }
        }

        stage('Pruebas y Linting') {
            steps {
                script {
                    // Similar al de .NET, usamos un contenedor temporal
                    // para correr pruebas o linting (como flake8 o pytest)
                    docker.image(PYTHON_IMAGE).inside {
                        sh 'pip install --no-cache-dir -r requirements.txt'
                        
                        // Aquí correrías tus herramientas de calidad de código:
                        // sh 'flake8 .'
                        // sh 'pytest'
                        echo 'Saltando pruebas y linting (configúralos aquí)...'
                    }
                }
            }
        }

        stage('Construir Imagen Docker') {
            steps {
                script {
                    // Exactamente igual que antes, le pedimos a Docker que 
                    // construya el Dockerfile en el directorio actual ('.')
                    def appImage = docker.build("${IMAGE_NAME}:${IMAGE_TAG}", '.')
                }
            }
        }

        stage('Push a Registry (Opcional)') {
            // Esta etapa solo se ejecuta si el build es en la rama 'main' o 'master'
            when { branch 'main' }
            
            steps {
                echo "Haciendo 'push' de ${IMAGE_NAME}:${IMAGE_TAG}..."
                // Ejemplo con credenciales
                // docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-credentials') {
                //    docker.image(IMAGE_NAME).push(IMAGE_TAG)
                // }
                
                echo "Simulación de push (configura tu registry aquí)..."
            }
        }
    }

    post {
        always {
            echo 'Pipeline finalizado.'
        }
    }
}