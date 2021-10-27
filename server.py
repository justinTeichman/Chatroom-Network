import signal
import sys
import random
import selectors
from socket import *

# This class represents the server for our tcp network

s_selectors = selectors.DefaultSelector()   # This selectors object will manage read events on the welcoming and tcp connection sockets
dictC = {}  # The dictionary will hold server end sockets that are connected to the clients


# signal handler that responds to control c from server
def signal_handler(sig,frame):  
    print('Interrupt recieved, shutting down ...')

    msg = 'DISCONNECT CHAT/1.0'

    # sends messages to all the clients telling them that the server is shutting down
    for key,value in dictC.items():
        dictC[key].send(msg.encode())

    sys.exit(0) # program terminates
    

# method processes and interprets the registration message
def proccessReg(msg,conn):
    temp = msg.split(' ')
    
    if temp[0] != 'REGISTER' or temp[2] != 'CHAT/1.0' or len(temp) != 3:    # case: registration message is out of format
        response = '400 Invalid registration'
    if temp[1] in dictC:    # case: user already exist in the network
        response = '401 Client already registered'
    else:   # case: registration is successfull
        response = '200 Registration successful'

    conn.send(response.encode())    # send response back to the client

    return response,temp[1] # returns response and user


# method accepts connection through welcoming socket and processes registration messages
def accept(sock,mask):      
    conn,addr = sock.accept()   # welcoming socket accepts connection from client
    reg_msg = conn.recv(100).decode()   
    res,user = proccessReg(reg_msg,conn)    # processes registration message and gets the user and response
    
    if(res != '200 Registration successful'):   # case: registration not successful
        conn.close()
    else:   # case: registration is successful
        dictC[user] = conn  # assigns serverside socket with the client user and stores in a dictionary
        print('Accepted connection from client address:',addr) 
        print('Connection to client established, waiting to recieve messages from',user, '...')

        s_selectors.register(conn,selectors.EVENT_READ,read) # since the tcp connection for the server and client is established 
        # the selectors object will now look and manage the server side socket


# method reads input from a client, manages the server related messages and communicates with other clients
def read(conn,mask): 
    data = conn.recv(100).decode()  # reads message from client

    for key,value in dictC.items(): # finds the user that sent this message by searching the dictionary
            if value == conn:
                user = key
    msg = '@%s:%s'%(user,data)  # creates the message to be sent to the other clients
    
    if data != 'DISCONNECT CHAT/1.0':   # case: successful registration
        print('Recieved message from @%s:'%(user),data)

        # relays the message to all the other clients
        for key,value in dictC.items():
            if key != user:
                dictC[key].send(msg.encode())

    else:   # case: client presses control c
        print('Recieved message from %s:'%(user),' DISCONNECT %s CHAT/1.0'%(user))
        print('Disconnecting user %s'%(user))
        dictC.pop(user) # remove server connected socket with its corresponding client
        s_selectors.unregister(conn)    # stop tracking the connection socket with the client that left the network
        conn.close()

        
def main():
    
    signal.signal(signal.SIGINT,signal_handler) # sets up the signal with its corresponding signal handler
    s_port = random.randint(49152,65535)    # sets port number in the reserve range of ports

    w_socket = socket(AF_INET,SOCK_STREAM)  # creates welcoming socket
    w_socket.bind(('',s_port))  # set host and port
    w_socket.listen()   # listen for accepting connections
    w_socket.setblocking(False)
    s_selectors.register(w_socket,selectors.EVENT_READ,accept)  #selectors object will track and report when a read event is being performed on the welcoming socket
    print('Will wait for client connections at port %d'%(s_port))

    # This code below will run through and report all events taking place on all tracked objects for as long as the program is running
    while True:
        events = s_selectors.select()
        for key,mask in events:
            call = key.data
            call(key.fileobj,mask)


if __name__ == '__main__':
    main()