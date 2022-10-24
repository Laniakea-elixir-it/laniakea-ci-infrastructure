FROM ubuntu:20.04

MAINTAINER Marco Tangaro, ma.tangaro@ibiom.cnr.it

# Append repository mirror to sources list
RUN echo "deb https://repo.data.kit.edu/ubuntu/22.04 ./" > /etc/apt/sources.list

# Install oidc-agent
RUN apt update -qq && apt install --no-install-recommends -y oidc-agent

# Download orchent package
ADD https://github.com/indigo-dc/orchent/releases/download/v1.2.8/orchent_1.2.8_amd64.deb /tmp/

# Install orchent
RUN dpkg -i /tmp/orchent_1.2.7-rc1_amd64.deb 
