#!/usr/bin/env python
import pika, time
import json

# Authenticate with RabbitMQ server
with open('rabbitmq-auth.json') as f:
    auth_data = json.load(f)
mq_creds  = pika.PlainCredentials(
    auth_data["username"], auth_data["password"])
mq_params = pika.ConnectionParameters(
    host         = auth_data["host"],
    credentials  = mq_creds,
    virtual_host = auth_data["vhost"],
    heartbeat_interval = auth_data["heartbeat"],
)

# This a connection object
connection = pika.BlockingConnection(mq_params)

# This is one channel inside the connection
channel = connection.channel()
# Setup the domenet exchange if it's not there.
channel.exchange_declare(exchange='domenet',
                         exchange_type='direct')

# Set consumer to receive status requests.
result = channel.queue_declare(exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='domenet',
                   routing_key='status',
                   queue=queue_name)

# If we recieve a status request, reply.
# TODO: Make this actually be smart once polling server is ready.
def callback(ch, method, properties, body):
  print(" [>] %r" % body)
  channel.basic_publish(exchange='domenet',
                      routing_key='status',
                      body='domelx.output Online')
  print(" [<] Replied to status request.")

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)


## Recieve data from DomeLX - domeoutput.pde
import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the output of domelx.
server_address = ('localhost', 1337)
print(' [*] domelx -> domenet bridge starting up on %s port %s. To exit press CTRL+C.' % server_address)
sock.bind(server_address)
print(' [*] Waiting to receive LED data from domelx.')
while True:

    data, address = sock.recvfrom(4096)

    print(' [>] Received %s bytes from %s' % (len(data), address))

    if data:
        channel.basic_publish(exchange='domenet',
                    routing_key='server',
                    body='data')

channel.start_consuming()
