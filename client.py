import signal
import sys
from socket import *
from urllib.parse import urlparse
import argparse
import selectors


c_selectors = selectors.DefaultSelector()   # This selectors object will manage read events on the stdin and tcp connection sockets
c_socket = socket(AF_INET, SOCK_STREAM)


# signal handler that responds to control c from server
def signal_handler(sig,frame):
    print('Interrupt recieved, shutting down ...')
    c_socket.send(('DISCONNECT CHAT/1.0').encode())
    c_socket.close()
    sys.exit(0)


# upon execution of the program this method will be will proccess the arguments
def arg_handler():
    parser = argparse.ArgumentParser()  # argparse object will used to seperate and evaluate the url
    parser.add_argument('name') # parse the url into the name and address
    parser.add_argument('address')

    argument = parser.parse_args()
    user = argument.name
    temp = argument.address
    loc = urlparse(temp)    # parse the address to abstravt hostname and port
    serverName = loc.hostname
    serverPort = loc.port
    return user,serverName,serverPort # returns username, hostname and port number in the execution of the program


# read method handles all the reading performed on the client side socket
def read(sock,mask):
    
    msg = sock.recv(1024).decode()
    if msg == 'DISCONNECT CHAT/1.0':    # case: server sends disconnect message
        print('\nDisconnected from server ... exiting!')
        sock.close()    # close the client side socket
        sys.exit(0)

    print('\n%s\n>'%(msg),end="",flush=True)    # outputs the message


#   upon user input this methods sends a message to the server
def send(inData,mask):  
    msg = inData.readline().rstrip()
    c_socket.send(msg.encode())
    print(">",end="",flush=True)
    

#   connects the socket with the server and handles bad address exception
def connect(sock,name,port):
    try:
        c_socket.connect((name,port))
    except ConnectionRefusedError:
        print('Invalid address\nPROGRAM IS TERMINATING')
        sys.exit(0)


def main():
    
    signal.signal(signal.SIGINT,signal_handler) # sets up the signal with its corresponding signal handler
    usr,name,port = arg_handler()   # call argument handler and records information
    print('Connecting to the server ...')
    connect(c_socket,name,port) # calls connect method

    print('Connection to server established. Sending intro message ...\n')
    msg = "REGISTER %s CHAT/1.O"%(usr)
    c_socket.send((msg).encode())   # sends registration message to client
    resp = c_socket.recv(1024).decode() # record client registration response

    if(resp != '200 Registration successful'):  #case: unsuccessful registration with the server
        print(resp,'... Disconnecting from the server') 
        print('program terminating')
        sys.exit(0)
    print('Registration successful. Ready for messaging!')
    
    c_selectors.register(c_socket,selectors.EVENT_READ,read)    # sets up read event with client side socket with the selectors
    c_selectors.register(sys.stdin,selectors.EVENT_READ,send)   # sets up read event with stdin object with the selectors

    print(">",end="",flush=True)

    # This code below will run through and report all events taking place on all tracked objects for as long as the program is running
    while True:
        events = c_selectors.select()
        for key,mask in events:
            call = key.data
            call(key.fileobj,mask)

        


if __name__ == '__main__':
    main()
