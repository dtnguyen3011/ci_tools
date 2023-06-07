## main image
FROM bcr-de01.inside.bosch.cloud/osd/osd5:latest

ENV DEBIAN_FRONTEND="noninteractive"
RUN unset http_proxy && apt-get update && \
	apt-get install -y --fix-missing apt-utils software-properties-common python3 python3-pip &&\
	apt-get upgrade -y

## Copy ci_tool into container
ENV WS=/var/jenkins/ws/tool/ci_tools
WORKDIR $WS
COPY . .
RUN python3 -m pip install -r /var/jenkins/ws/tool/ci_tools/requirements.txt --proxy=http://rb-proxy-de.bosch.com:8080
RUN whoami && pwd
