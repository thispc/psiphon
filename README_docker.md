Usage:

First Time:

Get Docker
https://www.docker.com

docker pull tanmaytat11/psiphon

docker run -d -it -p 127.0.0.1:1080:1080 --name psiphon tanmaytat11/psiphon

Subsequent runs:

docker start psiphon

docker exec -it psiphon bash

After that you will get access to the shell and can use all the psiphon commands. This method forwards all the docker's traffic on port 1080 (psiphon's default port) to the machine's 1080 port.

example: psiphon -e -r IN -i 1

To connect to India's first server and also exposing the proxy over the network.

psiphon -h
will open the help

After using the service you can disconnect by pressing ctrl + c and then ctrl + d to get out of shell. Finally you can stop the service by docker stop psiphon

Standard psiphon operations:

Usage: psiphon [options]


Options:
<br>
  -h ,     --help            show this help message and exit
  <br>
  -e ,     --expose          Expose SOCKS proxy to the network
   <br>
  -t ,     --test-servers    Test all servers
   <br>
  -r REGION,     --reg=REGION   Regions
   <br>
  -s ,     --show            Show available servers
   <br>
  -p PORT ,     --port=PORT  Local Port
   <br>
  -u ,     --update          Update Servers
   <br>
  -i SID ,     --sid=SID     Server number
   <br>
 <br>

PS: remember to use the -e option of psiphon otherwise it will not work
PPS: If you do not want to use my docker image, it is totally fine. You can create your own docker image with the help of the Dockerfile.
docker build -t psiphon .