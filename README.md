* If you get the error about libcrypto.so.1.0.0, You have to build a new ssh binary or just simply remove the ssh executable to avoid the error. It will automatically detect it and will connect with SSH instead of OSSH.
# psiphon

Psiphon is a circumvention tool from Psiphon Inc. that utilizes VPN, SSH and HTTP Proxy technology to provide you with uncensored access to Internet content. Your Psiphon client will automatically learn about new access points to maximize your chances of bypassing censorship.

Psiphon is designed to provide you with open access to online content. Psiphon does not increase your online privacy, and should not be considered or used as an online security tool. This is a multifunctional modified linux version of the original tool by Psiphon Inc.

Forked the pyclient from https://bitbucket.org/psiphon/psiphon-circumvention-system/

## Getting Started (Linux and Mac OS X 10.11 or older) (For Mac OS X (After 10.12) and Windows, instructions are at the end of this README)

```
$ git clone <repo url>
$ cd psiphon
```

### Prerequisites

Things needed to get it working.
- python 2.7 and above
- python-pip

```sh
$ sudo apt-get install python-pip
```

### Installing

A step by step guide :

- ##### Creating ssh binary

    However an ssh binary is provided for ubuntu 14.04, it is highly recommended to compile your ssh binary to remove compatibility issues. 
    
    ```sh
    psiphon$ cd openssh-5.9p1
    openssh-5.9p1$ ./configure
    ```
    
    Install the required dependencies if error occurs.
    Use make command after successful verification of dependencies.
    ```sh
    openssh-5.9p1$ make
    ```
    A ssh binary will be created on successful completion of make command.
    After removing existing binary file, copy the new binary to main psiphon folder.
    ```sh
    openssh-5.9p1$ cd ..
    psiphon$ rm ssh
    psiphon$ cp openssh-5.9p1/ssh .
    ```
    Your binary is ready for running.
    
- ##### Updating server list
    However a server list has been provided, it is highly recommended to update servers from time to time.
    
    ```sh
    psiphon$ python psi_client.py -u
    ```
    It requires Internet connection. If error occurs in the script, Use pip to install required packages.
    ##### Example:
    If error is "ImportError: No module named wget",
    Run the following command:
    ```sh
    $ sudo pip install wget
    ```
    etc.
    
    Upon successful completion, Use the following command to list all the servers.
    
    For obfuscated ssh (OSSH) servers only :
    ```sh
    psiphon$ python psi_client.py -s 
    ```
    For All servers including non obfuscated ssh ones :
    ```sh
    psiphon$ python psi_client.py -s -a 
    ```
    For further filtering region wise, add -r filter to the above commands.
    Ex, For India Servers (only ossh ones) :
    ```sh
    psiphon$ python psi_client.py -s -r IN
    ```
- ##### Final Step
    Use the Following command to run psiphon:
    ```sh
    psiphon$ python psi_client.py
    ```
    Connecting region wise (Lets say India):
    ```sh
    psiphon$ python psi_client.py -r IN
    ```
    These commands will establish a socks proxy on default port 1080.
    To change the default port use -p flag:
    ```sh
    psiphon$ python psi_client.py -r IN -p 1234
    ```
    To see all India servers add -s flag to the above commands:
    ```sh
    psiphon$ python psi_client.py -r IN -p 1234 -s
    ```
    
    To Connect to specific ip server with a serial number 2 from the above result:
    ```sh
    psiphon$ python psi_client.py -r IN -p 1234 -i 2
    ```
    
    In case of error:
    example- 
    "ImportError: No module named pexpect"
    ```sh
    $ sudo pip install pexpect
    ```
    Make alias for convenience:
    ```sh
    $ echo 'alias psiphon="cd ~/psiphon && python psi_client.py"' >> ~/.bashrc
    ```
    Now on a new terminal:
    ```sh
    $ psiphon -h
    $ psiphon
    ```
    Psiphon should now be running successfully on your machine.

## Commands:
```sh
psiphon$ python psi_client.py -h
```

```
Usage: psi_client.py [options]

Options:
  -h, --help            show this help message and exit
  -e, --expose          Expose SOCKS proxy to the network
  -t, --test-servers    Test all servers
  -r REGION, --reg=REGION
                        Regions
  -s, --show            Show available servers
  -p PORT, --port=PORT  Local Port
  -u, --update          Update Servers
  -i SID, --sid=SID     Server number
  -a, --all             Include Non OSSH servers also
```

## Testing servers
#### All servers:

```sh
psiphon$ python psi_client.py -t
```
#### Region Specific:
```sh
psiphon$ python psi_client.py -t -r IN
```

## Exposing Port
This can be used to share socks proxy created over a specific port.
#### Default (port 1080):
```sh
psiphon$ python psi_client.py -e
```
#### Specific (Ex- port 1234):
```sh
psiphon$ python psi_client.py -e -p 1234
```
# For Mac OS X (After 10.12) and Windows (Docker Instructions)

You can use the docker image of the psiphon client and run psiphon on any OS.

#### First Time:

```sh
Get Docker https://www.docker.com
```
```sh
docker pull thepsiphonguys/psiphon

docker run -d -it -p 127.0.0.1:1080:1080 --name psiphon thepsiphonguys/psiphon
```

#### Subsequent runs:

```sh
docker start psiphon

docker exec -it psiphon bash
```

After that you will get access to the shell and can use all the psiphon commands. This method forwards all the docker's traffic on port 1080 (psiphon's default port) to the machine's 1080 port.

To stop psiphon
```sh
docker stop psiphon
```

PS: remember to use the -e option of psiphon otherwise it will not work

PPS: You can also use docker on linux if you do not wan't to compile your own ssh binary. Docker is system independent.

PPPS: If you do not want to use our docker image, it is totally fine. You can create your own docker image with the help of the Dockerfile.
Refer to https://docs.docker.com/engine/reference/commandline/build/ for more details on how to build the docker image.
```sh
docker build -t psiphon .
```
