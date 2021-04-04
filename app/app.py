from flask import Flask, jsonify, request
from flask_caching import Cache
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
from flask_compress import Compress
import uuid
import conf
import constants
import pymysql.cursors
import pymongo
import datetime
from bson.objectid import ObjectId
from redis import Redis
from rq import Worker, Queue, Connection
import os
mongoclient = pymongo.MongoClient(constants.mongoclient)

tacpoint_db = mongoclient["tacpoint"]
tacpoint_col = tacpoint_db[conf.cluster_id]

app = Flask(__name__)
api = Api(app)
Compress(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

BASE_URL = '/v1/'

server = os.environ.get('REDIS_HOST')
redis_conn = Redis(server)
q = Queue(connection=redis_conn)

def open_connection():
    try:
        con = pymysql.connect(host=constants.DB_HOST, user=constants.DB_USER, password=constants.DB_PASSWORD, database=constants.DB_NAME, cursorclass=pymysql.cursors.DictCursor)

    except Exception as error:
        print(error)
    return con

@app.route(BASE_URL + 'ep/join', methods=['PUT'])
def endpoint_join():
    con = open_connection()
    data = request.get_json()
    print(data)
    ep_hostname = data['sysinfo']['hostname']
    x = tacpoint_col.insert_one(data['sysinfo'])
    sel_query = 'select * from endpoints where endpoint_id="{0}" and cluster_id="{1}"'.format(data['endpoint_id'], conf.cluster_id)
    query = 'insert into endpoints (endpoint_id, cluster_id, endpoint_hostname, last_connection, document_id) values ("{0}","{1}","{2}","{3}","{4}")'.format(data['endpoint_id'], conf.cluster_id, ep_hostname, data['timestamp'], x.inserted_id)
    update_query = 'update endpoints set endpoint_hostname="{0}", last_connection="{1}", document_id="{2}"'.format(ep_hostname, data['timestamp'], x.inserted_id)
    print(x.inserted_id)
    try:
        cur = con.cursor()
        row_count = cur.execute(sel_query)
        if row_count > 0:
            cur.execute(query)
        else:
            cur.execute(update_query)
        con.commit()
        cur.close()

    except Exception as error:
        print(error)
        return jsonify({'message': 'system error'}),500
    
    return jsonify({"message": 'ok'}),200


@app.route(BASE_URL + 'api/sysinfo/<ep_id>', methods=['GET'])
def get_EP_SysInfo(ep_id):
    con = open_connection()
    query = 'select * from endpoints where cluster_id="{0}" and endpoint_id="{1}"'.format(conf.cluster_id, ep_id)
    try:
        cur = con.cursor()
        cur.execute(query)
        res = cur.fetchall()
        cur.close()
    except Exception as error:
        print(error)
        return jsonify({"message": "error"})
    clusterid = conf.cluster_id
    resp = tacpoint_col.find_one({"_id": ObjectId(res[0]['document_id'])}, {'_id': False})
    print(resp)
    return jsonify({'sysinfo': resp})


@app.route(BASE_URL + 'ep/healthcheck/<ep_id>', methods=['PUT'])
def ep_healthCheck(ep_id):
    con = open_connection()
    data = request.get_json()
    print(data)
    ep_hostname = data['sysinfo']['hostname']
    x = tacpoint_col.insert_one(data['sysinfo'])
    task_sel = 'select * from task_list where cluster_id="{0}" and endpoint_id="{1}"'.format(conf.cluster_id, ep_id)
    update_query = 'update endpoints set endpoint_hostname="{0}", last_connection="{1}", document_id="{2}"'.format(ep_hostname, data['timestamp'], x.inserted_id)
    try:
        cur = con.cursor()
        cur.execute(update_query)
        con.commit()
        cur.execute(task_sel)
        res = cur.fetchall()
        cur.close()
    except Exception as error:
        print(error)
        return jsonify({'message': 'server error'}),500
    return jsonify({'message': 'ok', 'tasks': res}),200


@app.route(BASE_URL + 'api/getEndpoints', methods=['GET'])
def getEndpoints():
    con = open_connection()
    query = 'select * from endpoints where cluster_id="{0}"'.format(conf.cluster_id)
    try:
        cur = con.cursor()
        cur.execute(query)
        res = cur.fetchall()
        cur.close()

    except Exception as error:
        print(error)
        return jsonify({'message': 'server error'}),500
    return jsonify({'endpoints': res})

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=4444)
