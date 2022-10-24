FROM centos:7

MAINTAINER Marco Tangaro, ma.tangaro@ibiom.cnr.it

# Add repository
ADD https://repo.data.kit.edu/data-kit-edu-centos7.repo /etc/yum.repos.d/
RUN yum install -y epel-release

# Install oidc-agent
RUN yum install -y oidc-agent
ENV OIDC_AGENT=/usr/bin/oidc-agent

# Download orchent package
ADD https://github.com/indigo-dc/orchent/releases/download/v1.2.8/orchent-1.2.8-1.el7.x86_64.rpm /tmp/

# Install orchent
RUN rpm -i /tmp/orchent-1.2.8-1.el7.x86_64.rpm
