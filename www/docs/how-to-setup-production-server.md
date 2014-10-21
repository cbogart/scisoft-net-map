# Initial preparations
0. `sudo apt-get install python`
1. Install pip: `sudo apt-get install git python-setuptools python-pip python-virtualenv virtualenvwrapper` 
2. Add www user: `sudo useradd wwwuser -d /home/wwwuser -k /etc/skel -m -s /bin/bash -U`
3. Create a www folder: `sudo mkdir -p /var/www`
4. Create environment foler: `sudo mkdir /var/www/environments`
5. Goto /var: `cd /var`
6. Change ownership: `sudo chown -R wwwuser:wwwuser www`
7. Set up port forwarding from whatever port the server uses to 80: if it's 6543, then:
       'sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to 8080'

    (More info at: http://askubuntu.com/questions/427600/persist-port-routing-from-80-to-8080)

# The following steps should be done as `wwwuser`
1. Become `wwwuser`: `su - wwwuser`, use your root password
2. `cd /var/www/environments`
3. Create virtual environment: `virtualenv env`
4. Enter environment `. env/bin/activate`
5. Install Pyramide: `easy_install Pyramid`
6. `pip install numpy`
7. `pip install waitress`
8. Go to www root folder `cd /var/www`
9. Clone your project here: `git clone https://github.com/Tyumener/SNM.git`
10. Navigate to `cd SNM/www/SNM-web`
11. Install dependencies: `python setup.py develop`

At this point you could try to check if everything is correct.
Type `pserve development.ini` in `/var/www/SNM/www/SNM-web` folder. You should be able to navigate in your browser to `your-server.com:6543`

If you can see the snm application - you're on the right track.

# Make it run forever
```
pserve production.ini start --daemon --pid-file=/var/www/5000.pid \
--log-file=/var/www/5000.log --monitor-restart http_port=5000
```


P.S.
Is based on [http://akbarahmed.com/2012/08/08/install-pyramid-on-ubuntu-12-04-lts-rackspace/]

