import paho.mqtt.client as mqtt
import json
import sys
import time

data = {
    'pawfinder_id' : int(sys.argv[1]),
    'data' : {
        'latitude' : float(sys.argv[2]),
        'longitude' : float(sys.argv[3]),
    },
    'rssi' : float(sys.argv[4]),
    'timestamp' : time.time(),
    'msg_id' : sys.argv[1] + '-' + str(time.time())
}

def on_connect(client, userdata, flags, rc):
    print('Connected with result code:' + str(rc))

client = mqtt.Client()
client.on_connect = on_connect

client.connect('localhost', 1883, 60)

client.publish('forward', json.dumps(data))
