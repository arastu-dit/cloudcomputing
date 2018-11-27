import os
from flask import Flask, Response, request, redirect, url_for
from werkzeug import secure_filename
import urllib2
import boto
import boto.sqs
import boto.sqs.queue
from boto.sqs.message import Message
from boto.sqs.connection import SQSConnection
from boto.exception import SQSError
import sys
import json
from tempfile import mkdtemp
from subprocess import Popen, PIPE

app = Flask(__name__)

@app.route("/")
def index():
    return """
Available API endpoints:

GET /queues						List all queues
POST /queues					Create a new queue
DELETE /queues/<qid>				Delete a specific queue
GET /queues/<qid>/msgs			Get a message, return it to the user
GET /queues/<qid>/msg/count		Return the number of messages in a queue
POST /queues/<qid>/msgs 		Write a new message to a queue
DELETE /queues/<qid>/msgs 		Get and delete a message from the queue

"""

@app.route("/version", methods=['GET'])
def version():
	"""
	print boto version

	curl -s -X GET localhost:5000/version

	"""
	print("Boto version: "+boto.Version+ "\n")
	return "Boto version: "+boto.Version+ "\n"

@app.route("/queues", methods=['GET'])
def queues_index():
	"""
	List all queues

	curl -s -X GET -H 'Accept: application /json' http://localhost:5000/queues | python -mjson.tool
 	curl -s -X GET -H 'Accept: application /json' amazonServer:8080/queues | python -mjson.tool
	"""
	all = []
	conn = get_conn()
	for q in conn.get_all_queues():
		all.append(q.name)
	resp = json.dumps(all)
	return Response(response=resp, mimetype="application/json") 

@app.route("/queues", methods=['POST'])
def queues_create():
	"""
	Crete queue

	curl -X POST -H 'Content-Type: application/json' http://localhost:5000/queues -d '{"name": "D13123887"}'
	curl -X POST -H 'Content-Type: application/json' amazonServer:8080/queues -d '{"name": "D13123887"}'	
	
	"""

	conn = get_conn()
	body = request.get_json(force=True)
	name = body['name']
	queue = conn.create_queue(name, 120)
	resp = "Queue "+name+" has been created\n"
	return Response(response=resp, mimetype="application/json")

@app.route("/queues/<name>", methods=['DELETE'])
def queues_remove(name):
	"""
	Delete queue

	curl -X DELETE -H 'Accept: application/json' http://localhost:5000/queues/D13123887
	curl -X DELETE -H 'Accept: application/json' amazonServer:8080/queues/D13123887
	
	"""

	conn = get_conn()
	queue = conn.get_queue(name)
	conn.delete_queue(queue)
	
	resp = "Queue "+name+" has been removed\n"
	return Response(response=resp, mimetype="application/json")

@app.route("/queues/<name>/msgs/count", methods=['GET'])
def messages_count(name):
	"""
	Get message count for queue

	curl -X GET -H 'Accept: application/json' http://localhost:5000/queues/D13123887/msgs/count
	curl -X GET -H 'Accept: application/json' amazonServer:8080/queues/D13123887/msgs/count
	"""

	conn = get_conn()
	queue = conn.get_queue(name)
	count = queue.count()
	
	resp = "Queue "+name+" has "+str(count)+" messages\n"
	return Response(response=resp, mimetype="application/json")	

@app.route("/queues/<name>/msgs", methods=['POST'])
def messages_write(name):
	"""
	Writee message to queue

	curl -s -X POST -H 'Accept: application/json' http://localhost:5000/queues/D13123887/msgs -d '{"content": "Hello World!"}' 
	curl -s -X POST -H 'Accept: application/json' amazonServer:8080/queues/D13123887/msgs -d '{"content": "Hello World!"}'
	"""

	body = request.get_json(force=True)
	messageText = body['content']
	
	conn = get_conn()
	queue = conn.get_queue(name)
	queue.set_message_class(Message)
	m = Message()
	m.set_body(messageText)
	queue.write(m)
	
	resp = "Message "+messageText+" has been written to queue "+name+"\n"
	return Response(response=resp, mimetype="application/json")	


@app.route("/queues/<name>/msgs", methods=['GET'])
def messages_read(name):
	"""
	Get message from queue

	curl -X GET -H 'Accept: application/json' http://localhost:5000/queues/D13123887/msgs
	curl -X GET -H 'Accept: application/json' amazonServer:8080/queues/D13123887/msgs
	"""

	conn = get_conn()
	queue = conn.get_queue(name)
	messages = queue.get_messages()
	if len(messages) > 0:
		message = messages[0]
		resp = "Queue: "+name+". \nMessage: "+ message.get_body()+"\n"
	else:
		resp = "No messages for queue "+name+"\n"
	return Response(response=resp, mimetype="application/json")

@app.route("/queues/<name>/msgs", methods=['DELETE'])
def messages_consume(name):
	"""
	Consume message from queue

	curl -X DELETE -H 'Accept: application/json' http://localhost:5000/queues/D13123887/msgs
	curl -X DELETE -H 'Accept: application/json' amazonServer:8080/queues/D13123887/msgs
	"""

	conn = get_conn()
	queue = conn.get_queue(name)
	messages = queue.get_messages()
	if len(messages) > 0:
		message = messages[0]
		resp = "Queue: "+name+" \nDeleted message: "+ message.get_body()+" \n"
		queue.delete_message(message)
	else:
		resp = "No messages for queue "+name+"\n"
	return Response(response=resp, mimetype="application/json")

def get_conn():
	key_id, secret_access_key = urllib2.urlopen("http://ec2-52-30-7-5.eu-west-1.compute.amazonaws.com:81/key").read().split(':')
	return boto.sqs.connect_to_region("eu-west-1", aws_access_key_id=key_id ,aws_secret_access_key=secret_access_key)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000, debug=True)
