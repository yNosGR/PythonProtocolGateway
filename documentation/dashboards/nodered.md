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
1. Install influx `sudo apt install influxdb influxdb-client && sudo systemctl enable influxdb && sudo systemctl start  `
2. Create the `solar` db in influx `echo "CREATE DATABASE solar" | influx`
3. Drag an `InfluxDB Out Node` out into the workspace, connect a wire from the `mqtt in` node to the `InfluxDB Out` node. Double click the node, click the `+`, give it a name and the name of the database from above (solar). Click add. It will return you to the node setup, where you will give it a name and a measurement (`solar` in my setup), click `save` or `done`.

### TODO: create some nodes that consume the DB info.

## Create your flow or import the example flow (for EG4 users)
### Import example
Go to the hamburger, down to `Import`, click `select a file to import`, find `nodered-example-flow.json` in the repo. You should be left with something like this.
![example flow](https://github.com/user-attachments/assets/c2c284f8-e40f-4e05-bcb7-e054e32dad4c)

### Create your own flow
1. Drag a `debug` node out - we will be using this throughout to see how the data flows. You can see the debug output by dragging a wire from an output to the debug's input and turning it on.
2. Drag an `mqtt in` node out to the workspace. click the pencil to create a new mqtt-broker-node. Give it a name, enter the hostname in the server field (`solar.local` in our example), click security, add the username and password, click `add` orf `update`. Under `Topic`, enter `home/inverter`. Click done.
3. Drag a json node out onto the workspace, connect the input (left) side of the `json` node to the output of the `mqtt in` node.
4. For each of the things you want on the dashboard, add in a `function` node. This is to filter out the thing you want displayed, in this example, battery percentage. Drag a wire from the `json` node to the function you just created.
```
msg.payload = parseInt(msg.payload.battery_percentage);
return  msg;
```
click done.
4. From here on out, you will be setting up the wigets you want to see. Checkout the [flowfuse dashboard wiki](https://dashboard.flowfuse.com/getting-started.html) for more info.  For each of the functions you just created, create a `chart`, `gauge`, or `text` node to display the things the way you want them displayed. You will need to create a group and page node on the first, the ui will help you throuhg that.

## Edit the nginx config file to point at the dashboard
Use sudo and your favorite editor to edit `/etc/nginx/sites-enabled/default`. jump down to the `server_name _` section and replace everything between the `{` and `}` so it's like below.

```        server_name _;
                location / {
                include proxy_params;
                rewrite ^/(.*) /dashboard/$1 break;
                proxy_pass http://127.0.0.1:1880;
        }
``` 

You should now be able to browse to [Solar.local/Home](http://solar.local/Home/)

---
source: https://github.com/yNosGR/PythonProtocolGateway/blob/NodeRed_howto/NodeRed.MD