#!/usr/bin/env python

import os
import sys
import socket
import struct
import select
import time
import json
import pickle
import requests
import pprint

pp = pprint.PrettyPrinter(indent=4)

url = "http://localhost:8080/api/network/ping"
headers = {'Content-type': 'application/json',
            'Accept': 'application/vnd.sensor.jauu.net.v1+json'
          }

# From /usr/include/linux/icmp.h; your milage may vary.
ICMP_ECHO_REQUEST = 8 # Seems to be the same on Solaris.

FILE_PATH = "/tmp/foo.db"

def db_append_data(new_data):

    data = []
    if os.path.isfile(FILE_PATH):
        pkl_file = open(FILE_PATH, 'rb')
        data = pickle.load(pkl_file)
        pkl_file.close()

    data.append(new_data)

    output = open(FILE_PATH, 'wb')
    pickle.dump(data, output)
    output.close()

    file = open(FILE_PATH, 'a+')
    file.write("%s\n" % (data))
    file.close()

def db_append_data_arr(new_data):
    for i in new_data:
        db_append_data(i)


def db_get_data():
    if not os.path.isfile(FILE_PATH):
        return None
    pkl_file = open(FILE_PATH, 'rb')
    data = pickle.load(pkl_file)
    pkl_file.close()
    return data


def db_reset():
    if os.path.isfile(FILE_PATH):
        os.remove(FILE_PATH)

 
 
def checksum(source_string):
    sum = 0
    count_to = (len(source_string) / 2) * 2
    count = 0
    while count < count_to:
        thisVal = ord(source_string[count + 1]) * 256 + ord(source_string[count])
        sum = sum + thisVal
        sum = sum & 0xffffffff
        count = count + 2
 
    if count_to < len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff # Necessary?
 
    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
 
    return answer
 
 
def receive_one_ping(my_socket, ID, timeout):
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([my_socket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return
 
        timeReceived = time.time()
        recPacket, addr = my_socket.recvfrom(1024)
        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader
        )
        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent
 
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return
 
 
def send_one_ping(my_socket, dest_addr, ID):
    dest_addr  =  socket.gethostbyname(dest_addr)
 
    my_checksum = 0
 
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    bytesInDouble = struct.calcsize("d")
    data = (192 - bytesInDouble) * "Q"
    data = struct.pack("d", time.time()) + data
 
    my_checksum = checksum(header + data)
 
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
    )
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1
 
 
def do_one(dest_addr, timeout):
    """
    Returns either the delay (in seconds) or none on timeout.
    """
    icmp = socket.getprotobyname("icmp")
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error, (errno, msg):
        if errno == 1:
            # Operation not permitted
            msg = msg + (
                " - Note that ICMP messages can only be sent from processes"
                " running as root."
            )
            raise socket.error(msg)
        raise # raise the original error
 
    my_ID = os.getpid() & 0xFFFF
 
    send_one_ping(my_socket, dest_addr, my_ID)
    delay = receive_one_ping(my_socket, my_ID, timeout)
 
    my_socket.close()
    return delay
 
 
def ping(dest_addr, timeout = 10, count = 5):
    res = list()
    for i in xrange(count):
        print "ping %s..." % dest_addr,
        try:
            delay  =  do_one(dest_addr, timeout)
        except socket.gaierror, e:
            print "failed. (socket error: '%s')" % e[1]
            res.append(0)
 
        if delay  ==  None:
            print "failed. (timeout within %ssec.)" % timeout
            res.append(0)
        else:
            delay  =  int(delay * 1000)
            print "get ping in %dms" % delay
            res.append(delay)

    return res


def construct_data(host, measurement_data):
    data = dict()
    data["host"]      = host
    data["times"]     = measurement_data
    data["timestamp"] = int(time.time())
    return data


def sync_data(all_data):
    failed_sync_data = []
    for i in all_data:
        try:
            r = requests.post(url, data=json.dumps(i), headers=headers)
        except :
            failed_sync_data.append(i)
            continue
        print("Status Code:")
        print(r.status_code)
        print("")
        print("URL:")
        print(r.url)
        print("")
        print("Encoding:")
        print(r.encoding)
        print("")
        print("Content:")
        print(r.content)
        print("")
        if int(r.status_code) != 202:
            print("Failed to sync data")
            failed_sync_data.append(i)
            continue

    return failed_sync_data


def main(host):
    res = ping(host)

    json_data = construct_data(host, res)
    db_append_data(json_data)

    all_data = db_get_data()
    remain_data = sync_data(all_data)
    db_reset()
    if len(remain_data) > 0:
        print("Not all synced, save to DB")
        db_append_data_arr(remain_data)


if __name__ == '__main__':
    main("localhost")
