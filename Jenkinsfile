pipeline {
    agent any

    environment {
        APP_NAME        = "course-registration-app"
        IMAGE_NAME      = "course-registration-app"
        IMAGE_TAG       = "${BUILD_NUMBER}"
        CONTAINER_NAME  = "course-registration-container"
        APP_PORT        = "5000"
        HEALTH_ENDPOINT = "http://localhost:5000/health"
        VOLUME_NAME     = "course_registration_data"
    }

    options {
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    triggers {
        // Poll SCM every 5 minutes as an automated fallback when public webhooks cannot reach local Jenkins
        pollSCM('H/5 * * * *')
    }

    stages {

        stage('1. Checkout Source Code') {
            steps {
                echo "=========================================================="
                echo "STAGE 1: CHECKING OUT SOURCE CODE FROM GIT REPOSITORY"
                echo "=========================================================="
                checkout scm
                script {
                    echo "Build Number : ${env.BUILD_NUMBER}"
                    echo "Branch       : ${env.GIT_BRANCH ?: 'main'}"
                    echo "Commit Hash  : ${env.GIT_COMMIT ?: 'HEAD'}"
                }
            }
        }

        stage('2. Prepare Test Environment') {
            steps {
                echo "=========================================================="
                echo "STAGE 2: PREPARING PYTHON ENVIRONMENT & DEPENDENCIES"
                echo "=========================================================="
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
                echo "=========================================================="
                echo "STAGE 3: EXECUTING AUTOMATED PYTEST SUITE"
                echo "=========================================================="
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
                    // Record test results into Jenkins test dashboard
                    junit allowEmptyResults: true, testResults: 'test-results.xml'
                }
                failure {
                    echo "❌ ERROR: One or more automated tests failed!"
                    echo "Aborting pipeline: Application will NOT be built or deployed."
                }
            }
        }

        stage('4. Build Docker Image') {
            steps {
                echo "=========================================================="
                echo "STAGE 4: BUILDING DOCKER IMAGE [${IMAGE_NAME}:${IMAGE_TAG}]"
                echo "=========================================================="
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

        stage('5. Deploy Application Container') {
            steps {
                echo "=========================================================="
                echo "STAGE 5: DEPLOYING APPLICATION CONTAINER SAFELY"
                echo "=========================================================="
                script {
                    if (isUnix()) {
                        sh """
                            echo "Ensuring persistent SQLite database volume exists..."
                            docker volume create ${VOLUME_NAME} || true

                            echo "Gracefully stopping and removing any existing container..."
                            docker stop ${CONTAINER_NAME} || true
                            docker rm ${CONTAINER_NAME} || true

                            echo "Starting updated container [${CONTAINER_NAME}]..."
                            docker run -d \\
                                --name ${CONTAINER_NAME} \\
                                --restart unless-stopped \\
                                -p ${APP_PORT}:5000 \\
                                -v ${VOLUME_NAME}:/app/data \\
                                -e DATA_DIR=/app/data \\
                                -e SECRET_KEY=production-jenkins-secure-key \\
                                ${IMAGE_NAME}:${IMAGE_TAG}
                        """
                    } else {
                        bat """
                            docker volume create ${VOLUME_NAME} 2>nul || ver >nul
                            docker stop ${CONTAINER_NAME} 2>nul || ver >nul
                            docker rm ${CONTAINER_NAME} 2>nul || ver >nul
                            docker run -d --name ${CONTAINER_NAME} --restart unless-stopped -p ${APP_PORT}:5000 -v ${VOLUME_NAME}:/app/data -e DATA_DIR=/app/data -e SECRET_KEY=production-jenkins-secure-key ${IMAGE_NAME}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('6. Verify Deployment Health') {
            steps {
                echo "=========================================================="
                echo "STAGE 6: VERIFYING DEPLOYMENT VIA /health ENDPOINT"
                echo "=========================================================="
                script {
                    if (isUnix()) {
                        sh """
                            echo "Probing ${HEALTH_ENDPOINT} for healthy status..."
                            MAX_RETRIES=12
                            RETRY_COUNT=1
                            DEPLOY_SUCCESS=0

                            while [ \$RETRY_COUNT -le \$MAX_RETRIES ]; do
                                echo "Health check probe \$RETRY_COUNT of \$MAX_RETRIES..."
                                HTTP_CODE=\$(curl -s -o health_output.json -w "%{http_code}" ${HEALTH_ENDPOINT} || echo "000")
                                
                                if [ "\$HTTP_CODE" = "200" ]; then
                                    echo "✅ Health check PASSED with HTTP 200 OK!"
                                    cat health_output.json
                                    echo ""
                                    DEPLOY_SUCCESS=1
                                    break
                                else
                                    echo "Probe returned HTTP \$HTTP_CODE. Retrying in 5 seconds..."
                                    sleep 5
                                fi
                                RETRY_COUNT=\$((RETRY_COUNT + 1))
                            done

                            if [ \$DEPLOY_SUCCESS -ne 1 ]; then
                                echo "❌ CRITICAL ERROR: Application failed health verification."
                                echo "=== Container Logs ==="
                                docker logs --tail 100 ${CONTAINER_NAME} || true
                                exit 1
                            fi
                        """
                    } else {
                        // Windows agent health probe using python one-liner with retry loop
                        bat """
                            python -c "import time, urllib.request, json, sys; max_tries=12; [print(f'Probe {i+1}...') or (time.sleep(5) if (lambda: [False] if True else [])() else None) or ((urllib.request.urlopen('${HEALTH_ENDPOINT}', timeout=5).getcode() == 200 and (print('Health check PASSED!') or sys.exit(0))) if True else None) for i in range(max_tries)]; sys.exit(1)"
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "=========================================================="
            echo "🎉 PIPELINE SUCCESS: Deployment completed and verified!"
            echo "Access application at: http://localhost:${APP_PORT}"
            echo "Health endpoint      : ${HEALTH_ENDPOINT}"
            echo "=========================================================="
        }
        failure {
            echo "=========================================================="
            echo "❌ PIPELINE FAILED: See stage output above for diagnostics."
            echo "=========================================================="
        }
        always {
            cleanWs deleteDirs: false, notFailBuild: true, patterns: [[pattern: 'venv/**', type: 'EXCLUDE']]
        }
    }
}
