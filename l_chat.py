#!/usr/bin/env python3
# encoding: utf-8
import socket
from threading import Thread
import threading
import sys,os,signal
import time
import struct
import base64
from hashlib import sha1
import requests
from multiprocessing import Queue

CLIENT = {
    "CLIENT_LOG_HEAD":"[CLIENT] "
}

SERVER = {
    "SERVER_BACKLOG":5,
    "WELCOME_MESSAGE":"Welcome to L-Chat!",
    "SERVER_LOG_HEAD":"[SERVER] "
}

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg=msg.encode('utf-8')
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen).decode("utf-8", "ignore")

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

#class watcher
class Watcher:
    global client
    global server
    def __init__(self):
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            print(" ")
            print("[EXIT] Control-C")
            self.kill()
        sys.exit()

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError: pass



def get_connect_info():
    host = input("Connect Host:");
    port = int(input("Connect port:"))
    server_port = int(input("Server port:"))
    if port < 1 or port > 65535:
        return -1
    if server_port < 1 or server_port > 65535:
        return -1
    return {"host":host,"port":port,"server_port":server_port}

class chat_client(Thread):
    global cnt_info
    global CLIENT
    def init_(self):
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        self.cnt_info=cnt_info
        self.queue = Queue()
        send_msg_to = threading.Thread(target=self.send_msg_to)
        send_msg_to.setDaemon(True)
        send_msg_to.start()
        while True:
            msg=input()
            if msg[:2]=="/q":
                break
            if msg=="":
                continue
            self.queue.put(msg)

    def send_msg_to(self):
        while True:
            if self.queue.qsize() == 0:
                time.sleep(0.01)
                continue
            msg=self.queue.get()
            msg2=str("["+socket.gethostname()+"]: "+msg)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.host = self.cnt_info["host"]
            self.port = self.cnt_info["port"]
            try:
                self.s.connect_ex((self.host, self.port))
                send_msg(self.s, msg2)
                #print("Me: "+msg)
                self.s.close()
            except:
                try:
                    self.s.close()
                except:
                    pass
            finally:
                self.s.close()

class chat_server(Thread):
    global SERVER
    global cnt_info
    def init_(self):
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        self.s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = get_host_ip()
        self.port = cnt_info["server_port"]
        self.s.bind((self.host, self.port))
        recv_msg_from = threading.Thread(target=self.recv_msg_from)
        recv_msg_from.setDaemon(True)
        recv_msg_from.start()

    def recv_msg_from(self):
        self.s.listen(SERVER["SERVER_BACKLOG"])
        while True:
            #print(SERVER["SERVER_LOG_HEAD"]+"listen!")
            c, addr = self.s.accept()
            #print(SERVER["SERVER_LOG_HEAD"]+"Connect Address:"+str(addr[0]))
            print(str(recv_msg(c)))
            c.close()
        self.s.close()

if __name__=="__main__":
    flag=0
    Watcher()

    client=chat_client()
    server=chat_server()

    print("Welcome to L-chat!")
    print("Your IP Address: "+get_host_ip())
    print("",end="\n")
    while flag==0:
        cnt_info = get_connect_info()
        if cnt_info!=-1:
            print("Connect informations:"+str(cnt_info))
            flag=1
        else:
            print(" ")
            print("ERROR:"+str(cnt_info))
            print(" ")


    server.start()
    #pdb.set_trace()
    time.sleep(3)
    client.start()
