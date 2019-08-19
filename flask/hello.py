from flask import Flask
from flask import escape
from flask import request
from flask import abort
from flask import jsonify
from flask import make_response
from flask import Response
from flask_mqtt import Mqtt
from flask_cors import CORS, cross_origin
import pymongo
import json
from bson.json_util import dumps
from bson.objectid import ObjectId

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADER'] = 'Content-Type'
app.config['MQTT_BROKER_URL'] = '0.0.0.0'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_BROKER_REFRESH_TIME'] = 1.0
mqtt = Mqtt(app)

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('#')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    recv_topic = message.topic
    recv_data = message.payload.decode('utf-8')
    
    print(recv_topic, recv_data)

    if recv_topic == 'forward':
        print('\nFORWARD TOPIC\n')
        json_data = json.loads(recv_data)
        print(json_data)
        pawfinder_id = json_data['pawfinder_id']
        print('pawfinder_id:', pawfinder_id)

        if pawfinder_id:
            client = pymongo.MongoClient()
            db = client.pawfinder
            
            animal = db.animals.find_one({'pawfinder_id' : pawfinder_id})
            print(animal)
            user = db.users.find_one({'_id':ObjectId(animal['user_id'])})

            print(user)
            print('User ID:', user['_id'])
            mqtt.publish(str(user['_id']), '1')

            db.location.insert_one({
                'animal_id' : str(animal['_id']),
                'latitude' : json_data['data']['latitude'],
                'longitude' : json_data['data']['longitude'],
                'rssi' : json_data['rssi'],
                'msg_id' : json_data['msg_id'],
                'timestamp' : json_data['timestamp']
            })


@app.route('/')
@cross_origin()
def hello():
    return 'Hello world!'

@app.route('/test')
@cross_origin()
def test():
    print('test')
    return 'test'

@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    client = pymongo.MongoClient()
    db = client.pawfinder

    json_data = request.get_json()
    print(json_data)
    username = json_data['username']
    user_data = db.users.find_one({'username':username})

    data_to_return = {
        'user_id' : str(user_data['_id'])        
    }

    if user_data:
        return make_response(jsonify(data_to_return), 200)
    else:
        print('aborting')
        abort(400)

@app.route('/location')
@cross_origin()
def location():
    client = pymongo.MongoClient()
    db = client.pawfinder
    
    user_id = request.args.get('user_id')
    
    animals_data = db.animals.find({'user_id':user_id})

    loc_latest_array = []
    
    for animal in animals_data:
        location_latest = db.location.find({'animal_id':str(animal['_id'])}).limit(1).sort([('$natural', -1)])
        loc_latest_array.append(location_latest)

    return Response(dumps(loc_latest_array), status=200, mimetype='application/json')

@app.route('/locations')
@cross_origin()
def locations():
    client = pymongo.MongoClient()
    db = client.pawfinder
    
    animal_id = request.args.get('animal_id')

    limit = None

    try:
        limit = int(request.args.get('limit'))
    except:
        print('No limit')

    locations_data = db.location.find({'animal_id':animal_id}).sort([('$natural', -1)])

    if limit:
        locations_data = locations_data[:limit]

    return Response(dumps(locations_data), status=200, mimetype='application/json')
    # return dumps(locations_data)


@app.route('/animal', methods=['POST'])
@cross_origin()
def insert_animal():
    client = pymongo.MongoClient()
    db = client.pawfinder
    
    data_json = request.get_json()
    user_id = data_json['user_id']
    name = data_json['name']
    animal_type = data_json['animal_type']
    pawfinder_id = data_json['pawfinder_id']
    
    animal_data = db.animals.find({'user_id' : user_id})

    db.animals.insert_one({
        'user_id' : user_id,
        'name' : name,
        'animal_type' : animal_type,
        'pawfinder_id' : pawfinder_id
    })

    return 'Add success'


@app.route('/user', methods=['POST'])
@cross_origin()
def insert_user():
    client = pymongo.MongoClient()
    db = client.pawfinder
    
    data_json = request.get_json()
    name = data_json['name']
    username = data_json['username']

    _id = db.users.insert_one({
        'name' : name,
        'username' : username,
    })
    return str(_id.inserted_id) 

@app.route('/user', methods=['GET'])
@cross_origin()
def get_user():
    client = pymongo.MongoClient()
    db = client.pawfinder
    
    user_id = request.args.get('user_id')

    user_data = db.users.find_one({'_id' : ObjectId(user_id)})
    return Response(dumps(user_data), status=200, mimetype='application/json')

@app.route('/users', methods=['GET'])
@cross_origin()
def get_users():
    client = pymongo.MongoClient()
    db = client.pawfinder
    
    user_data = db.users.find()
    return dumps(user_data)

@app.route('/animals', methods=['GET'])
@cross_origin()
def get_animals():
    client = pymongo.MongoClient()
    db = client.pawfinder
    
    user_id = request.args.get('user_id')

    animals_data = db.animals.find({'user_id':user_id})
    return Response(dumps(animals_data), status=200, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
