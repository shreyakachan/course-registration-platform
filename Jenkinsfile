pipeline {
    agent any

    environment {
        APP_NAME        = 'course-registration-platform'
        IMAGE_NAME      = 'course-registration-platform'
        IMAGE_TAG       = "${BUILD_NUMBER}"
        CONTAINER_NAME  = 'course-registration-container'
        APP_PORT        = '5000'
        HEALTH_ENDPOINT = 'http://localhost:5000/health'
        VOLUME_NAME     = 'course_registration_data'
    }

    options {
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    triggers {
        // Poll GitHub repository every 5 minutes when external webhooks cannot reach local Jenkins
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('1. Checkout GitHub Source') {
            steps {
                echo '=========================================================='
                echo 'STAGE 1: CHECKING OUT SOURCE CODE FROM GITHUB'
                echo '=========================================================='
                checkout scm
                script {
                    echo "Build Number : ${env.BUILD_NUMBER}"
                    echo "Git Branch   : ${env.GIT_BRANCH ?: 'main'}"
                    echo "Git Commit   : ${env.GIT_COMMIT ?: 'HEAD'}"
                }
            }
        }

        stage('2. Validate Python Project and Install Dependencies') {
            steps {
                echo '=========================================================='
                echo 'STAGE 2: PREPARING PYTHON ENVIRONMENT & DEPENDENCIES'
                echo '=========================================================='
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m venv venv || python -m venv venv
                            . venv/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        '''
                    } else {
                        bat '''
                            python -m venv venv
                            call venv\\Scripts\\activate.bat
                            python -m pip install --upgrade pip
                            python -m pip install -r requirements.txt
                        '''
                    }
                }
            }
        }

        stage('3. Run Automated Tests') {
            steps {
                echo '=========================================================='
                echo 'STAGE 3: EXECUTING AUTOMATED PYTEST SUITE'
                echo '=========================================================='
                script {
                    if (isUnix()) {
                        sh '''
                            . venv/bin/activate
                            pytest -v --junitxml=test-results.xml tests/
                        '''
                    } else {
                        bat '''
                            call venv\\Scripts\\activate.bat
                            python -m pytest -v --junitxml=test-results.xml tests/
                        '''
                    }
                }
            }
            post {
                always {
                    // Archive JUnit test report in Jenkins dashboard
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
                failure {
                    echo '❌ AUTOMATED TESTS FAILED: Halting pipeline immediately.'
                    echo 'Deployment safety gate activated: No Docker image will be built or deployed.'
                }
            }
        }

        stage('4. Build Docker Image') {
            steps {
                echo '=========================================================='
                echo "STAGE 4: BUILDING DOCKER IMAGE [${IMAGE_NAME}:${IMAGE_TAG}]"
                echo '=========================================================='
                script {
                    if (isUnix()) {
                        sh """
                            docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .
                        """
                    } else {
                        bat """
                            docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .
                        """
                    }
                }
            }
        }

        stage('5. Deploy New Application Version') {
            steps {
                echo '=========================================================='
                echo 'STAGE 5: DEPLOYING DOCKER CONTAINER WITH PERSISTENCE'
                echo '=========================================================='
                script {
                    if (isUnix()) {
                        sh """
                            echo "Ensuring persistent SQLite database volume [${VOLUME_NAME}] exists..."
                            docker volume create ${VOLUME_NAME} || true

                            echo "Gracefully stopping and removing any previous container..."
                            docker stop ${CONTAINER_NAME} || true
                            docker rm ${CONTAINER_NAME} || true

                            echo "Launching updated container [${CONTAINER_NAME}]..."
                            docker run -d \\
                                --name ${CONTAINER_NAME} \\
                                --restart unless-stopped \\
                                -p ${APP_PORT}:5000 \\
                                -v ${VOLUME_NAME}:/app/data \\
                                -e DATA_DIR=/app/data \\
                                -e FLASK_CONFIG=production \\
                                -e SECRET_KEY=production-jenkins-secure-key-2026 \\
                                ${IMAGE_NAME}:${IMAGE_TAG}
                        """
                    } else {
                        bat """
                            docker volume create ${VOLUME_NAME} 2>nul || ver >nul
                            docker stop ${CONTAINER_NAME} 2>nul || ver >nul
                            docker rm ${CONTAINER_NAME} 2>nul || ver >nul
                            docker run -d --name ${CONTAINER_NAME} --restart unless-stopped -p ${APP_PORT}:5000 -v ${VOLUME_NAME}:/app/data -e DATA_DIR=/app/data -e FLASK_CONFIG=production -e SECRET_KEY=production-jenkins-secure-key-2026 ${IMAGE_NAME}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('6. Verify Application Health') {
            steps {
                echo 'STAGE 6: VERIFYING APPLICATION HEALTH'

                script {
                    if (isUnix()) {
                        sh '''
                    for i in $(seq 1 12); do
                        echo "Health probe $i of 12..."
                        if curl -fsS --max-time 5 "$HEALTH_ENDPOINT" > /dev/null; then
                            echo "Health check PASSED: HTTP 200"
                            exit 0
                        fi
                        if [ "$i" -lt 12 ]; then sleep 5; fi
                    done
                    echo "Health check FAILED"
                    docker logs --tail 100 "$CONTAINER_NAME"
                    exit 1
                '''
            } else {
                        powershell '''
                    $url = $env:HEALTH_ENDPOINT
                    for ($i = 1; $i -le 12; $i++) {
                        Write-Output "Health probe $i of 12..."
                        try {
                            $r = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
                            if ([int]$r.StatusCode -eq 200) {
                                Write-Output "Health check PASSED: HTTP 200"
                                exit 0
                            }
                        } catch {
                            Write-Output "Probe failed: $($_.Exception.Message)"
                        }
                        if ($i -lt 12) {
                            Start-Sleep -Seconds 5
                        }
                    }
                    Write-Output "Health check FAILED"
                    docker logs --tail 100 $env:CONTAINER_NAME
                    exit 1
                '''
                    }
                }
            }
        }

        stage('7. Report Final Build Status') {
            steps {
                echo '=========================================================='
                echo 'STAGE 7: PIPELINE EXECUTION SUMMARY & TELEMETRY'
                echo '=========================================================='
                script {
                    echo "Application Name : ${APP_NAME}"
                    echo "Deployed Image   : ${IMAGE_NAME}:${IMAGE_TAG}"
                    echo "Application URL  : http://localhost:${APP_PORT}"
                    echo "Health Endpoint  : ${HEALTH_ENDPOINT}"
                    echo "Data Volume      : ${VOLUME_NAME} (Persistent)"
                }
            }
        }
    }

    post {
        success {
            echo '🎉 PIPELINE SUCCESSFUL: Code verified, tested, built, and deployed!'
        }
        failure {
            echo '❌ PIPELINE FAILED: Inspect stage output and logs above.'
        }
        always {
            cleanWs deleteDirs: false, notFailBuild: true, patterns: [[pattern: 'venv/**', type: 'EXCLUDE']]
        }
    }
}
