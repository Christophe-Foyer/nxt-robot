import socket 

def socketClient(host, port, message):
    #sends message and returns data
    #host = 'localhost' 
    #port = 50000 
    size = 1024 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    s.connect((host,port)) 
    s.send(message)
    data = s.recv(size) 
    s.shutdown(socket.SHUT_RDWR)
    s.close() 
    return data


def socketServer(port, return_message):
    #this should be run in its own thread
    host = '' 
    backlog = 5 
    size = 1024 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host,port)) 
    s.listen(backlog)
    client, address = s.accept() 
    data = client.recv(size)
    if return_message: 
        client.send(return_message)
    client.close()
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    return data

#for testing
#print "waiting for data"
#message = 'received'
#data = socketServer(3210, message)
#print data

