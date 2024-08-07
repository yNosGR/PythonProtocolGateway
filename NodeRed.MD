# Setting up PythonProtocolGateway on a RasPi with NodeRed Dashboard 2.0
This is a simple how-to on setting up a Rasperry Pi node, attempting to be as copy/pastable as possible. As we stand on the shoulders of giants, I will refer to external how-tos for some of the steps. They did it better than I could anyway.

## Requirements
- a multicore raspberry pi. Though you can run it on a classic raspi 2/pi zero w, a pi zero 2 is the minimum for stablility.
- a recent version of raspberry pi os.

## Install Raspberry Pi OS
[Just like it says on the tin](https://www.raspberrypi.com/documentation/computers/getting-started.html#install-an-operating-system). Throughout this, I will use some conventions assuming you used the hostname Solar, the username is Solar, and the password is SolarPowered. The rest of this doc assumes you are SSHed in using PuTTY (for windows users) or a terminal of your choice (for the rest of us heathens). The hostname will be `solar.local`, username `solar`, and password `SolarPowered`

## install dependencies
`sudo apt update && sudo apt upgrade && sudo apt install tmux git mosquitto nginx`

## Configure Mosquitto MQTT server
Using your favorite text editor, add these lines to `/etc/mosquitto/mosquitto.conf`

```
listener 1883

allow_anonymous false 
password_file /etc/mosquitto/passwd

```
Create a new `mosquitto` password file while adding an mqtt user `sudo mosquitto_passwd -c /etc/mosquitto/passwd solar` - to add another user later, drop the `-c`. Start the service with `sudo systemctl start mosquitto`, set the service to start on boot with `sudo systemctl enable mosquitto`. 

## Download/configure PythonProtocolGateway
### Download 
`mkdir ~/src/ && cd ~/src && git clone https://github.com/HotNoob/PythonProtocolGateway.git` 
### Configure
[Follow the wiki](https://github.com/HotNoob/PythonProtocolGateway/wiki)

## Install/configure NodeRed service
### Install
[Install how-to](https://nodered.org/docs/getting-started/raspberrypi) - As of the 6 August 2024, you can just paste in `bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)`

## install NodeRed Nodes
1. [Log in.](http://solar.local:1880/)
2. Click the hambuger menu. 
3. Go to `Manage palette`. 
4. Under the `Install` tab, search for `@flowfuse/node-red-dashboard`. Click `Install`.
5. Optional: Under the `Install` tab, search for `node-red-contrib-influxdb`, click `Install`.

## Optional: Install/Enable InfluxDB
If you want to do some historical logging, InfluxDB is a better solution than the node-red internal db.
`sudo apt install influxdb && sudo systemctl enable influxdb && sudo systemctl start  

## Create your flow or import the example flow (for EG4 users)
### Import example
Goi to the hamburger, down to `Import`, click `select a file to import`, find `nodered-example-flow.json` in the repo.

### Create your own flow
1. Drag an `mqtt in` node out to the workspace. click the pencil to create a new mqtt-broker-node. Give it a name, enter the hostname in the server field (`solar.local` in our example), click security, add the username and password, click `add` orf `update`. Under `Topic`, enter `home/inverter`. Click done.
hh
2. Drag a json node out onto the workspace, connect the input (left) side of the `json` node to the output of the `mqtt in` node.
3. For each of the things you want on the dashboard, add in a `function` node. this is to filter out the thing you want displayed, in this example, battery percentage.
```
msg.payload = parseInt(msg.payload.battery_percentage);
return  msg;
```
click done.

