FROM ubuntu:14.04

MAINTAINER Tanmay Gupta <tanmay.tat11@gmail.com> Pulkit Chawla <pulkitchawl@gmail.com>

RUN apt-get update

RUN apt-get -y install git

RUN git clone https://github.com/thispc/psiphon.git /root/psiphon

RUN apt-get -y install python

RUN apt-get -y install python-setuptools

RUN easy_install pexpect

RUN easy_install wget

RUN echo 'alias psiphon="cd ~/psiphon && python psi_client.py"' >> ~/.bashrc

RUN /bin/bash -c "source ~/.bashrc"

EXPOSE 1080
