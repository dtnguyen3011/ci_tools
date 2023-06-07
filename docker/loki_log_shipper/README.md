Flask app to export logs to Loki via native push endpoint.
Returns HTTP 204 immediately and spawns subprocess to handle the log export asynchronously

Deploy managed by Jenkins job  
https://rb-jmaas.de.bosch.com/radar_customer_gen5/job/Ops/job/opsLokiShipperDeploy/

### Requires following environment variables to run:
  - JENKINS_USER (required)
  - JENKINS_PASSWORD (required)
  - BATCH_SIZE  : Number of lines sent in one HTTP connection. Default is 1000.
  - LOKI_URL    : (required) full URL of Loki's push endpoint example: http://abts55144.de.bosch.com:3100/loki/api/v1/push
  - DRY_RUN     : print payload to stdout instead of sending it (default value is False)

### The application exposes two endpoints

  '/health' : returns 'OK' if application is up
  '/' : is for triggering of the log export and requires two parameters jobUrl and jobName
        jobURL is the absolute URL of the Jenkins build such as http://127.0.0.1:8080/job/VAG/job/dbLibTest/253/
        jobName is the display name of the job as it will appear in the Loki tags
        example of the request: 127.0.0.1:5000/?jobUrl=https://127.0.0.1:443/job/VAG/job/dbLibTest/253/&jobName=VAG/dbLibTest

### Build image:
Image was built by CI when changes in directory detected

**DONT FORGET TO UPDATE VERSION IN FILE version**

For building we use prebuilt base image with necessary system packages

If you want to add system package(s) or update python version:
 1. add your changes to `Dockerfile.base`
 2. you need to build base image in your own computer via command:
`docker build -t bcr-de01.inside.bosch.cloud/radar_gen5/loki-shipper-base:<your tag> -f Dockerfile.base .`
 3. push image `docker push bcr-de01.inside.bosch.cloud/radar_gen5/loki-shipper-base:<your tag>`
 4. change instruction `FROM` in Dockerfile to your version of base image
 5. commit and push changes
 6. Merge to master

### Build image for testing
1. Remove `Deploy` stage from `Jenkinsfile`
2. Setup version in file version with test tag
3. Follow instruction Build image, without merging to master
4. Create job with pipeline from your branch

### Rollback
1. go to server via ssh
2. go to directory with loki-shipper(on `abts55144.de.bosch.com` `/opt/loki-shipper`)
3. change `LS_VERSION` in file `.env`
4. do `docker-compose up -d`