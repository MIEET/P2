#IoT API
#Ana Moreira
#30/06/2019

from flask import jsonify, abort, request, render_template, make_response
from pymongo import MongoClient
import pandas as pd
import gmplot
from flask import Flask
from flask_selfdoc import Autodoc

client = MongoClient()                                  #create a MongoClient instance
IoT_db = client.IoT2                                    #select database
thing = IoT_db.thing                                    #select collection

app = Flask(__name__)
things_counter = 0
auto = Autodoc(app)
#========================================================== Things ============================================================#

@app.route('/iot/api/v1.0/things/', methods=['GET'])
@auto.doc()
def get_things():
    """
    Retrieves a list of all things with their description into the website
    """
    output = []
    for data in thing.find():
        output.append({'thing_id': data['thing_id'], 'description': data['description'], 'location': data['location'],
              'sensors': data['sensors'[:]]})
    return render_template('things.html', items=output)

@app.route('/iot/api/v1.0/things/<int:thing_id>', methods=['GET'])
@auto.doc()
def get_one_thing(thing_id):
    """
    Retrieves feature's thing choosen by user
    """
    output = []
    data = thing.find_one({'thing_id': thing_id})                         #cursor
    if len(data) == 0:
        abort(404)
    output.append({'thing_id': data['thing_id'], 'description': data['description'], 'location': data['location'],
              'sensors': data['sensors'[:]]})

    return render_template('things.html', items=output)

@app.route('/iot/api/v1.0/things/map/<int:thing_id>', methods=['GET'])
@auto.doc()
def get_map(thing_id):
    """
    Retrieves a map with thing's location
    """

    results = list(thing.find({'thing_id': thing_id}))
    if len(results) == 0:
        abort(404)
    x = results[0]['location'][0]['coordinates']
    latitude_list = [x[0]]
    longitude_list = [x[1]]

    gmap3 = gmplot.GoogleMapPlotter(x[0], x[1], 18)

    # scatter points on the google map
    gmap3.scatter(latitude_list, longitude_list, '#FCF805', size=40, marker=False)
    gmap3.draw(r"D:\PC Backup\Universidade\Engenharia Electrónica e Telec\MEEE\2018_2019\ADAM\Prática\Projeto2\templates\map.html")

    return render_template('map.html', x=thing_id)

@app.route('/iot/api/v1.0/thing', methods=['POST'])
@auto.doc()
def create_thing():
    """
    Creates a thing in the dB
    """
    global things_counter
    doc = list(thing.find({}))                                            #check if database is empty
    if doc:
        newest_id = list(thing.find({}).sort([('thing_id', -1)]).limit(1))
        id_nr = newest_id[0]['thing_id']
        things_counter = id_nr + 1
    else:
        things_counter = 1

    if not request.json or not 'description' in request.json:
        abort(400)

    new_data = {
                'thing_id': things_counter,
                'description': request.json['description'],
                'location': request.json['location'],
                'sensors': request.json['sensors']
    }
    print(new_data)
    th_id = thing.insert_one(new_data)                                     #add to collection thing in IoT dB
    new_thing = thing.find_one({'_id': th_id.inserted_id})
    print(new_thing)
    output = {'thing_id': new_thing['thing_id'], 'description': new_thing['description'], 'location': new_thing['location'],
              'sensors': new_thing['sensors'[:]]}

    return jsonify({'result': output}), 201                               #status code 201, which HTTP defines as the code for "Created"

@app.route('/iot/api/v1.0/things/<int:thing_id>', methods=['PUT'])
@auto.doc()
def update_thing(thing_id):
    """
    Updates a thing in the dB
    """
    thing.find_one_and_update(
        {"thing_id": thing_id},
        {'$set': {
            'description': request.json['description'],
            'location': request.json['location'],
            'sensors': request.json['sensors']
                  }
        }
    )
    return "", 200

@app.route('/iot/api/v1.0/things/<int:thing_id>', methods=['DELETE'])
@auto.doc()
def delete_thing(thing_id):
    """
    Deletes a thing in the dB
    """
    delete_thing = thing.delete_one({'thing_id': int(thing_id)})
    if delete_thing.deleted_count > 0:
        return "", 204
    else:
        return "", 404


@app.route('/documentation')
def documentation():
    return auto.html()

#========================================================== Errors ============================================================#

@app.errorhandler(404) #Gives error message when any invalid url are requested
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400) #Gives error message when any bad requests are made
def not_found(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

#=========================================================== Main =============================================================#

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)