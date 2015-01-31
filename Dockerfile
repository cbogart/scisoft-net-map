FROM ubuntu
MAINTAINER Chris Bogart <cbogart@cs.cmu.edu>
RUN apt-get update
RUN apt-get install -y python python-dev python-setuptools python-pip
RUN mkdir /scisoft
ADD . /scisoft/
RUN easy_install "pyramid==1.5.1"
RUN pip install numpy
WORKDIR /scisoft/www/SNM-web
RUN python setup.py develop
EXPOSE 8888
CMD pserve --reload --monitor-restart development.R.ini
