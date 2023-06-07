import java.lang.Process
import javax.mail.Session
import javax.mail.Transport
import javax.mail.internet.InternetAddress
import javax.mail.internet.MimeMessage
import jenkins.model.Jenkins
import hudson.model.User
import hudson.model.Run
import java.util.logging.Logger
import hudson.model.StringParameterValue
import hudson.model.ParametersAction
import org.jenkinsci.plugins.workflow.graph.FlowGraphWalker
import org.jenkinsci.plugins.workflow.graph.FlowNode

protected class InfluxDBPoint {
    private String measurement
    private long timestamp
    public HashMap fields = [:]
    public HashMap tags = [:]

    public InfluxDBPoint(String measurement, long timestamp = java.lang.System.currentTimeMillis()) {
        this.measurement = measurement
        this.timestamp = timestamp
    }

    private String tagsToString(HashMap tags) {
        if (!tags.size()) { return '' }
        return tags.collect { key, value -> /${key}=${value}/ }.join(',')
    }

    private String fieldsToString(HashMap fields) {
        if (!fields.size()) { return '' }
        return fields.collect { key, value ->
            if (value.class == String)  {
                /${key}="${value}"/
            } else if (value.class == Integer) {
                /${key}=${value}i/
            } else {
                /${key}=${value}/
            }
        }.join(',')
    }

    private String mapToString(HashMap m) {
        if (!m.size()) {
            return ''
        }
        return m.collect { key, value ->
            value.class == String ? /${key}="${value}"/ : /${key}=${value}/
        }.join(',')
    }

    public String toString(boolean newApproach = false) {
        if (newApproach) {
            String tagsString = tagsToString(this.tags)
            tagsString = tagsString ? ',' + tagsString : tagsString
            String fieldsString = fieldsToString(this.fields)
            return "${this.measurement}${tagsString} ${fieldsString} ${this.timestamp}"
        }
        String tagsString = mapToString(this.tags)
        tagsString = tagsString ? ',' + tagsString : tagsString
        String fieldsString = mapToString(this.fields)
        return "${this.measurement}${tagsString} ${fieldsString} ${this.timestamp}"
    }
}

protected class InfluxDBWriter {
    private String influxURL
    private String influxDB
    public int retries = 3
    public long influxWaitTime = 2000
    public String influxUser
    public String influxPassword
    private String credentialsID
    private boolean influxHealthy
    protected static Logger log = Logger.getLogger(InfluxDBWriter.class.getName())

    public InfluxDBWriter(String influxURL, String influxDB, String credentialsID = null) {
        this.influxURL = influxURL
        this.influxDB = influxDB
        this.credentialsID = credentialsID

        if (credentialsID) {
            def creds = com.cloudbees.plugins.credentials.CredentialsProvider.lookupCredentials(
                com.cloudbees.plugins.credentials.common.StandardUsernameCredentials.class,
                Jenkins.instance,
                null,
                null
            ).find { it.id == this.credentialsID }
            this.influxUser = creds.username
            this.influxPassword = creds.password.getPlainText()
        }

        this.influxHealthy = influxDBHealthCheck()
    }

    public boolean influxDBHealthCheck() {
        URLConnection healthCheckConnection = new URL("${this.influxURL}/health").openConnection()
        healthCheckConnection.setConnectTimeout(1000)
        healthCheckConnection.setReadTimeout(1000)
        try {
            String output = healthCheckConnection.getInputStream().getText()
            def outputJson = new groovy.json.JsonSlurper().parseText(output)
            assert outputJson.status == "pass"
            this.log.info('Health check success! InfluxDB is available!')
            return true
        } catch(SocketTimeoutException socketTimeoutException) {
            this.log.info('Health check has reached timeout! Push to InfluxDB will be skipped!')
            return false
        } catch(Exception exception) {
            this.log.info('Health check has failed! Push to InfluxDB will be skipped!')
            return false
        }
    }

    private void pushMetrics(List<InfluxDBPoint> points, String customRetentionPolicy = null, boolean nanoseconds = false, boolean newApproach = false) {
        if (this.influxHealthy) {
            int attempts = 0
            while (attempts++ < this.retries) {
                StringBuilder stdOut = new StringBuilder()
                StringBuilder stdErr = new StringBuilder()
                String credentials = this.credentialsID ? "-u \'${this.influxUser}:${this.influxPassword}\' " : ''
                String retentionPolicyReference = customRetentionPolicy ? "&rp=${customRetentionPolicy}" : ''
                String precisionFlag = nanoseconds ? "" : "&precision=ms"
                String dataBinary = ""
                for(InfluxDBPoint point in points) {
                    dataBinary += point.toString(newApproach) + "\n"
                }
                String curlCommand = "curl ${credentials}-iks -XPOST \'${this.influxURL}/write?db=${this.influxDB}" \
                                     + retentionPolicyReference + precisionFlag + "\' --data-binary \'${dataBinary}\'"
                this.log.info(curlCommand)
                Process process = ['bash', '-c', curlCommand].execute()
                process.consumeProcessOutput(stdOut, stdErr)
                process.waitForOrKill(this.influxWaitTime)
                this.log.info(stdOut.toString())
                this.log.info(stdErr.toString())
              	
                if (stdOut.length() > 0 && stdOut.split()[1] == '204') {
                    break
                }
            }
        } else {
            this.log.info('Metric will not be pushed as InfluxDB is not healthy')
        }
    }

    private void runQuery(String query, String customRetentionPolicy = null) {
        if (this.influxHealthy) {
            int attempts = 0
            while (attempts++ < this.retries) {
                StringBuilder stdOut = new StringBuilder()
                StringBuilder stdErr = new StringBuilder()
                String credentials = this.credentialsID ? "-u \'${this.influxUser}:${this.influxPassword}\' " : ''
                String retentionPolicyReference = customRetentionPolicy ? "&rp=${customRetentionPolicy}" : ''
                String curlCommand = "curl ${credentials}-iks -XPOST \'${this.influxURL}/query?db=${this.influxDB}" \
                                    + retentionPolicyReference + "\'" + " --data-urlencode \"q=${query}\""
                this.log.info(curlCommand)
                Process process = ['bash', '-c', curlCommand].execute()
                process.consumeProcessOutput(stdOut, stdErr)
                process.waitForOrKill(this.influxWaitTime)
                this.log.info(stdOut.toString())
                this.log.info(stdErr.toString())
              log.info(stdOut.toString())
                            log.info(stdErr.toString())
                if (stdOut.length() > 0 && stdOut.split()[1] == '200') {
                    break
                }
            }
        } else {
            this.log.info('Query will not run as InfluxDB is not healthy')
        }
    }
}

def getPipelineName(def obj) {
    if (obj.parent.class == hudson.model.Hudson || obj.parent.class == com.cloudbees.hudson.plugins.folder.Folder) {
        return obj.getFullName()
    }
    return getPipelineName(obj.parent)
}

public void getQueueTimeByTask(Run build, InfluxDBWriter writer, long timestamp, String commitId) {
    FlowGraphWalker walker = new FlowGraphWalker(build.getExecution())
    for (FlowNode flowNode : walker) {
        nodeName = flowNode.getDisplayName()
        if (nodeName == 'Allocate node : Body : Start') {
            bodyStartTime = flowNode.getAction(org.jenkinsci.plugins.workflow.actions.TimingAction).getStartTime()
            bodyAllocationTime = flowNode.getEnclosingBlocks()[0].getAction(org.jenkinsci.plugins.workflow.actions.TimingAction)
                                         .getStartTime()
            timeInQueue = bodyStartTime - bodyAllocationTime
            label = flowNode.getEnclosingBlocks()[0].getAction(org.jenkinsci.plugins.workflow.cps.actions.ArgumentsActionImpl)
                            .getArguments()
            node = flowNode.getEnclosingBlocks().find {
                it.getDisplayName().startsWith('Branch:')
            }
            nodeName = node ? node.getDisplayName() : 'unknown'
            timestamp = timestamp * (10 ** (19 - timestamp.toString().length())) + (env.BUILD_ID + flowNode.id).toInteger()
            InfluxDBPoint queueTimeBySubtaskPoint = new InfluxDBPoint('jenkins_queue_time_per_node_new', timestamp)
            pipelineName = getPipelineName(build).replace(' ', '\\ ').replace('\\', '\\\\')
            branchSuffix = env.JOB_NAME.minus(pipelineName).replace('%2F', '/')
          	if (branchSuffix.startsWith('/')) {
          		branchSuffix = branchSuffix.substring(1)
          	}

            queueTimeBySubtaskPoint.tags.putAll([
                pipelineName: pipelineName,
                label       : (label.label ? label.label.replace('\\', '\\\\').replace(' ', '\\ ') : 'any')
            ])
            queueTimeBySubtaskPoint.fields.putAll([
                buildId    : env.BUILD_ID.toInteger(),
                branchName : branchSuffix,
                commit_id  : commitId,
                lucxLabel  : nodeName,
                stageId    : flowNode.id.toInteger(),
                timeInQueue: timeInQueue.toInteger(),
            ])

            log.info(">>>" + queueTimeBySubtaskPoint.toString(true))
            writer.pushMetrics([queueTimeBySubtaskPoint], null, true, true)
        }
    }
}

public void getPullRequestBuildStatistics(Run build, InfluxDBWriter writer, long timestamp, String commitId) {
    InfluxDBPoint pullRequestsBuildStatisticsPoint = new InfluxDBPoint('pull_request_builds_statistics', timestamp)

    String pullRequestNumber = env.JOB_NAME.split('/')[-1].split('-')[-1]
    int buildId = env.BUILD_ID.toInteger()
    String buildCauses = build.getCauses()[0].getShortDescription()
    // use displayName instead of JOB_NAME to be consistent with KPI collector jobs
    String jobNameCut = build.getFullDisplayName().replace(" » ", "/").split(' #')[0].minus("/PR-${pullRequestNumber}")
    long buildDuration = build.getDuration()
    String buildResult = build.getResult()
    String buildUrl = build.getAbsoluteUrl().minus("/job/PR-${pullRequestNumber}/${buildId}/")
    List<String> failureReasons = build.getLog().findAll(/\[ERROR\].*failed with message \'.*\'/)
                                    .collect { failureReason ->
        failureReason -= ~/\[ERROR\]./
        failureReason.replace("'", "\\\"")
    }
    String failureReasonsString = failureReasons.isEmpty() ? "n/a" : failureReasons.join('; ')

    pullRequestsBuildStatisticsPoint.fields.putAll([
        pr_number     : pullRequestNumber,
        build_id      : buildId,
        build_causes  : buildCauses,
        commit_id     : commitId,
        job_name      : jobNameCut,
        build_duration: buildDuration,
        result        : buildResult,
        failure_reason: failureReasonsString,
        build_url     : buildUrl
    ])

    log.info(pullRequestsBuildStatisticsPoint.toString())
    writer.pushMetrics([pullRequestsBuildStatisticsPoint])
}

public void getHWNodesFails(Run build, InfluxDBWriter writer, long timestamp, String commitId) {
    InfluxDBPoint hwFailsPoint = new InfluxDBPoint('hw_node_fails', timestamp)

    (matcher) = (build.getLog() =~ /Running on.*?(INT_TEST_.*?)\sin/).findAll()
    String buildNode = matcher[1]
    Integer buildResultCode
    if (build.result.toString() == 'SUCCESS') {
        buildResultCode = 0
    } else {
        buildResultCode = 1
    }
    hwFailsPoint.tags.putAll([
        hw_node: buildNode
    ])
    hwFailsPoint.fields.putAll([
        status     : "\"${build.result}\"",
        result_code: buildResultCode,
        commit_id  : commitId
    ])

    log.info(hwFailsPoint.toString())
    writer.pushMetrics([hwFailsPoint])
}

public void getMaxTimeInQueue(Run build, InfluxDBWriter writer, long timestamp, String commitId) {
    InfluxDBPoint queuingActionPoint = new InfluxDBPoint('jenkins_timingActions', timestamp)

    maxTimeInQueue = build.getActions(jenkins.metrics.impl.SubTaskTimeInQueueAction.class).max {
        it?.getQueuingDurationMillis()
    }

    if (maxTimeInQueue) {
        queuingActionPoint.tags.putAll([
            jobName: env.JOB_NAME
        ])
        queuingActionPoint.fields.putAll([
            status            : "\"${build.result}\"",
            buildId           : env.BUILD_ID.toInteger(),
          	commit_id  		  : commitId,
            subtaskQueuingTime: maxTimeInQueue.getQueuingDurationMillis(),
        ])

        log.info(queuingActionPoint.toString())
        writer.pushMetrics([queuingActionPoint])
    }
}


public void triggerLokiShipperTest(String jobName, String jobUrl, String commitId) {
    if (healthCheckLokiShipperTest(jobName, jobUrl)) {
        int attempts = 0
      	while (attempts++ < 3) {
            stdOut = new StringBuilder()
            stdErr = new StringBuilder()
            String curlCommand = "curl -iks -XPOST \'http://abts55144.de.bosch.com:5555/?jobUrl=${jobUrl}&jobName=${jobName}&commitId=${commitId}\'"
            log.info(curlCommand)
            process = ['bash', '-c', curlCommand].execute()
            process.consumeProcessOutput(stdOut, stdErr)
            process.waitForOrKill(1000)
            log.info(stdOut.toString())
            log.info(stdErr.toString())
            if (stdOut.length() > 0 && stdOut.split()[1] == '204') {
                break
            }
        }
    }
}

public void triggerLokiShipper(String jobName, String jobUrl, String commitId) {
    if (healthCheckLokiShipper(jobName, jobUrl)) {
        int attempts = 0
      	while (attempts++ < 3) {
            stdOut = new StringBuilder()
            stdErr = new StringBuilder()
            String curlCommand = "curl -iks -XPOST \'http://abts55144.de.bosch.com:5000/?jobUrl=${jobUrl}&jobName=${jobName}&commitId=${commitId}\'"
            log.info(curlCommand)
            process = ['bash', '-c', curlCommand].execute()
            process.consumeProcessOutput(stdOut, stdErr)
            process.waitForOrKill(1000)
            log.info(stdOut.toString())
            log.info(stdErr.toString())
            if (stdOut.length() > 0 && stdOut.split()[1] == '204') {
                break
            }
        }
    }
}

public boolean healthCheckLokiShipper(String jobName, String jobUrl) {
    URLConnection healthCheckConnection = new URL("http://abts55144.de.bosch.com:5000/health").openConnection()
    healthCheckConnection.setConnectTimeout(1000)
    healthCheckConnection.setReadTimeout(1000)
    try {
        String output = healthCheckConnection.getInputStream().getText()
        assert output.trim() == 'OK'
        log.info('Health check success! Loki Shipper is available!')
        return true
    } catch(SocketTimeoutException socketTimeoutException) {
    	log.info('Health check has reached timeout! Loki Shipper will not be triggered!')
        sendEmailNotification('Loki Shipper unavailable warning', "Loki Shipper instance http://abts55144.de.bosch.com:5000 " \
                              + "has reached timeout for healthcheck. Loki Shipper was not triggered for the job ${jobUrl}")
        return false
    } catch(Exception exception) {
        log.info('Health check has failed! Loki Shipper will not be triggered!')
        sendEmailNotification('Loki Shipper unavailable warning', "Loki Shipper instance http://abts55144.de.bosch.com:5000 " \
                              + "has failed healthcheck with output ${exception.toString()}. Loki Shipper was not triggered " \
                              + "for the job ${jobUrl}")
        return false
    }
}

public boolean healthCheckLokiShipperTest(String jobName, String jobUrl) {
    URLConnection healthCheckConnection = new URL("http://abts55144.de.bosch.com:5555/health").openConnection()
    healthCheckConnection.setConnectTimeout(1000)
    healthCheckConnection.setReadTimeout(1000)
    try {
        String output = healthCheckConnection.getInputStream().getText()
        assert output.trim() == 'OK'
        log.info('Health check success! Loki Shipper is available!')
        return true
    } catch(SocketTimeoutException socketTimeoutException) {
    	log.info('Health check has reached timeout! Loki Shipper will not be triggered!')
        sendEmailNotification('Loki Shipper unavailable warning', "Loki Shipper instance http://abts55144.de.bosch.com:5555 " \
                              + "has reached timeout for healthcheck. Loki Shipper was not triggered for the job ${jobUrl}")
        return false
    } catch(Exception exception) {
        log.info('Health check has failed! Loki Shipper will not be triggered!')
        sendEmailNotification('Loki Shipper unavailable warning', "Loki Shipper instance http://abts55144.de.bosch.com:5555 " \
                              + "has failed healthcheck with output ${exception.toString()}. Loki Shipper was not triggered " \
                              + "for the job ${jobUrl}")
        return false
    }
}

public void sendEmailNotification(String subject, String text) {
    InternetAddress[] recipients = InternetAddress.parse("xcdaradarcontinuousx@bosch.com, xcdaradarcontinuousxepam@bosch.com")
    def mailDescriptor = Jenkins.instance.getDescriptor("hudson.tasks.Mailer")
    Session session = mailDescriptor.createSession()
//
    MimeMessage msg = new MimeMessage(session)
    msg.setFrom(mailDescriptor.getAdminAddress())
    msg.setRecipients(MimeMessage.RecipientType.TO, recipients)
    msg.setSubject(subject)
    msg.setText(text)

    Transport transporter = session.getTransport("smtp")
    transporter.connect()
    transporter.send(msg)
}

public void sendEmailNotificationTest(String subject, String text) {
    InternetAddress[] recipients = InternetAddress.parse("external.kanstantsin.novichuk@de.bosch.com")
    def mailDescriptor = Jenkins.instance.getDescriptor("hudson.tasks.Mailer")
    Session session = mailDescriptor.createSession()

    MimeMessage msg = new MimeMessage(session)
    msg.setFrom(mailDescriptor.getAdminAddress())
    msg.setRecipients(MimeMessage.RecipientType.TO, recipients)
    msg.setSubject(subject)
    msg.setText(text)

    Transport transporter = session.getTransport("smtp")
    transporter.connect()
    transporter.send(msg)
}

String getBuildCommitId() {
	log.info("Finding sourceCommitId(${env.JOB_NAME} - ${env.BUILD_ID})")
	try {
      	// Finding buildinfo file log and get content
		String sourceCommitId
		String artifactDir = build.getArtifactsDir()
		for (artifact in build.getArtifacts()) {
			if (artifact.relativePath.endsWith("__buildinfo.log")) {
				String filePath = "${artifactDir}/${artifact.relativePath}"
				File file = new File(filePath)
				if (file.exists()) {
					sourceCommitId = file.getText('UTF-8')
				}
			}
		}
		
		// Parsing to find commit id
		if (sourceCommitId && sourceCommitId.contains("COMMIT:")) {
			sourceCommitId = sourceCommitId.substring(sourceCommitId.indexOf("COMMIT:")).split(" ")[1]
			sourceCommitId = sourceCommitId.substring(0, 8)
			log.info("Found sourceCommitId(${env.JOB_NAME} - ${env.BUILD_ID}):" + sourceCommitId)
			return sourceCommitId
		}
	} catch (Exception exception) {
		log.info("Exception in sourceCommitId(${env.JOB_NAME} - ${env.BUILD_ID}): ${exception.toString()}")
	}
	log.info("Not found sourceCommitId(${env.JOB_NAME} - ${env.BUILD_ID})")
	return ""
}

public void main() {
    boolean enableMonitoring = true
    boolean BFAEnabled = false
    log.info("Fired event '${event}' for build #${env.BUILD_ID}.")

    // Run checks only on jobs end
    if (event == 'RunListener.onFinalized' && enableMonitoring && !env.JOB_NAME.toLowerCase().startsWith('test')) {
        build = Jenkins.instance.getItemByFullName("${env.JOB_NAME}").getBuild("${env.BUILD_ID}")
        timestamp = run.getStartTimeInMillis()
        InfluxDBWriter ccdaInfluxDBWriter = new InfluxDBWriter('http://abtv55170.de.bosch.com:8086', 'ccda_radar')
        InfluxDBWriter ccdaGELInfluxDBWriter = new InfluxDBWriter('http://abtv55170.de.bosch.com:8086', 'ccda_radar_gel')
        // if (!ccdaInfluxDBWriter.influxHealthy) {
        //    sendEmailNotification('InfluxDB unavailable warning', "InfluxDB instance ${ccdaInfluxDBWriter.influxURL} " \
        //                          + "has failed healthcheck. Metrics for the job ${env.JOB_NAME} will not be pushed ")
        //}
      
      // pass it as an argument to avoid calling the function inside every method. significant load decrease
      	String commitId = getBuildCommitId()

        if (env.JOB_NAME.toLowerCase().startsWith('vag')) {
            // Collect Queue waiting time statistics per subtask
            getQueueTimeByTask(build, ccdaGELInfluxDBWriter, timestamp, commitId)
            // Trigger log collection to Loki
            triggerLokiShipperTest(env.JOB_NAME, build.getAbsoluteUrl(), commitId)
            triggerLokiShipper(env.JOB_NAME, build.getAbsoluteUrl(), commitId)
        }
      
        // Max time that build spent in the queue
        getMaxTimeInQueue(build, ccdaGELInfluxDBWriter, timestamp, commitId)

        // Hardware Nodes monitoring
        if (env.JOB_NAME in ["VAG/SW_Build/MT/HW_MT_LRR", "VAG/SW_Build/MT/HW_MT_MRR",
                             "VAG/SW_Build/MT/MT_GEN_HARDWARE_SMOKE_TEST_MRR",
                             "VAG/SW_Build/MT/MT_GEN_HARDWARE_SMOKE_TEST_LRR"]) {
            getHWNodesFails(build, ccdaGELInfluxDBWriter, timestamp, commitId)
        }

        // PR builds statistics monitoring
        if (env.JOB_NAME.split('/')[-1].startsWith('PR-')) {
            getPullRequestBuildStatistics(build, ccdaGELInfluxDBWriter, timestamp, commitId)
        }
    } else if (event == 'QueueListener.onEnterWaiting') {
        // log.info("Fired event ${event} for item ${item}")
        InfluxDBWriter ccdaInfluxDBWriter = new InfluxDBWriter('http://abtv55170.de.bosch.com:8086', 'ccda_radar_gel')
        long timestamp = item.getInQueueSince()
        InfluxDBPoint queuingLiveDataPoint = new InfluxDBPoint('jenkins_queue_live_data', timestamp)
        long taskId = item.getId()
      	String label = item.getAssignedLabel().name
        String jobName = item.task.getFullDisplayName().replace(" » ", "/")
        String buildId = ""

        if (jobName.contains('#')) {
            (jobName, buildId) = jobName.split(' #')
        }
        if (jobName.startsWith('part of ')) {
            jobName = jobName.minus('part of ')
        }

        queuingLiveDataPoint.tags.putAll([
            task_id       : taskId,
            label         : label
        ])

        queuingLiveDataPoint.fields.putAll([
            job_name      : jobName,
            build_id      : buildId
        ])

        // log.info(queuingLiveDataPoint.toString())
        ccdaInfluxDBWriter.pushMetrics([queuingLiveDataPoint], 'one_day')
      
      
    } else if (event == 'QueueListener.onLeft') {
        // log.info("Fired event ${event} for item ${item}")
        InfluxDBWriter ccdaInfluxDBWriter = new InfluxDBWriter('http://abtv55170.de.bosch.com:8086', 'ccda_radar_gel')
        String measurement = 'jenkins_queue_live_data'

        long taskId = item.getId()
        String deleteFromLiveQueue = "DELETE FROM \"${measurement}\" WHERE \"task_id\" = \'${taskId}\'"

        // log.info(deleteFromLiveQueue)
        ccdaInfluxDBWriter.runQuery(deleteFromLiveQueue, 'one_day')
    }
}

main()
