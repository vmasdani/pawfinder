import serial
import sys
import time
import json
from datetime import datetime
import paho.mqtt.client as mqtt

ser_port = sys.argv[1]
print(ser_port)

def on_connect(client, userdata, flags, rc):
    print('Connected with result code' + str(rc))


if __name__ == '__main__':
    client = mqtt.Client('gateway-client')
    client.on_connect = on_connect

    client.connect('0.0.0.0', 1883, 60)
    client.loop_start()

    with serial.Serial(ser_port, 115200, timeout=1) as ser:
        while(True):
            try:
                serial_data = ser.readline().decode('utf-8')
                # print(serial_data)

                if(serial_data): # Check if not empty
                    print('Received on: {}'.format(datetime.now()))
                    try:
                        data_json = json.loads(serial_data)
                        current_timestamp = int(datetime.timestamp(datetime.now()))
                        data_json['msg_id'] = '{}-{}'.format(data_json['pawfinder_id'], current_timestamp)
                        data_json['timestamp'] = current_timestamp
                        print(json.dumps(data_json, indent=4))

                        if((data_json['pawfinder_id'] !=  0) and (data_json['data']['latitude'] !=  0) and (data_json['data']['longitude'] !=  0) and (data_json['rssi'] != 0)):
                            print('Publishing...')

                            client.publish('forward', payload=json.dumps(data_json))
                        else:
                            print('Numbers invalid!')
                    except Exception as e:
                        print('error:', e)
                        print('Not a JSON!')
                        print(serial_data)
                    

            except KeyboardInterrupt:
                print('Exiting...')
                sys.exit(1)
            except Exception as e:
                print(e)
                print('Decode failed!')
