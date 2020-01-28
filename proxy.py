# web proxy to restrict access to http websites based on url and content
# skip check on jpg, gif, ico and png types 

import socket, sys
from _thread import *

HOST = '127.0.0.1'
PORT = 65432
BADLIST = [b"spongebob", b"britney spears", b"paris hilton", b"norrkoping"]
BADURL = "http://zebroid.ida.liu.se/error1.html"
BADCONTENT = "http://zebroid.ida.liu.se/error2.html"
SKIPTYPES = [b".jpg", b".gif", b".ico", b".png"]


def main():
    PORT = int(input("Enter port to connect to: "))

    # create socket for client to connect to
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(20)
    except Exception as e:
        print(e, " Failed to create socket")
        sys.exit(1)
        
    while True:
        conn, addr = s.accept()
        start_new_thread(process, (conn, addr))

    print("Shut down")
    s.close()


def process(conn, addr):
    data = conn.recv(80000)
    first_line = data.split(b"\r\n")[0]
    method = first_line.split(b" ")[0]
    url = first_line.split(b" ")[1]
    print(url)

    # checks for forbidden words in url, then redirect to error page 
    if checklist(url):
        redirect_link = redirect(BADURL)
        conn.shutdown(socket.SHUT_RD)
        conn.send(redirect_link.encode('ASCII'))

    else:
        # gets server and port number
        temp = extract(url)
        server, server_port = temp[0], temp[1]

        # create new socket to connect to server
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server, server_port))
            print("Connected")
            sock.send(data)

            while True:
                new_data = sock.recv(16000)
                if new_data != b'':
                    # checks for forbidden words in content, or for file extensions to skip                # present)
                    if checkskip(url) or not checkdata(new_data):
                        conn.send(new_data)

                    else:
                        # redirect to error page
                        redirect_link = redirect(BADCONTENT)
                        sock.shutdown(socket.SHUT_RD)
                        conn.shutdown(socket.SHUT_RD)
                        conn.send(redirect_link.encode('ASCII'))

        except Exception as e:
            print(e, " Failed to establish connection to server")
            sys.exit(4)

    conn.close()


# format url, return server and port number extracted from request 
def extract(url):
    if b"://" in url:
        pos = url.find(b"://")
        url = url[pos + 3:]

    if b":" in url:
        pos = url.find(b":")
        server = url[:pos]
        server_port = int(url.split(b":")[1].split(b"/")[0].decode('ASCII'))

    # if port can't be found, use defualt port 80
    else:
        server_port = 80
        server = url

    if b"/" in server:
        pos = server.find(b"/")
        server = server[:pos]

    return [server, server_port]


# redirect to error page, type specifies forbidden url or forbidden content 
def redirect(type):
    return ("HTTP/1.1 302 Found\r\nLocation: " + type + "\r\nHost: " + "zebroid.ida.liu.se" + "\r\nConnection: close\r\n\r\n")


# check url for forbidden words
def checklist(url):
    new_url = url.lower()

    for name in BADLIST:
        if b' ' in name:
            name = name.replace(b' ', b'')
        if name in new_url:
            return True
    return False

# check content for forbidden words
def checkdata(data):
    datastring = data.lower()
    lines = datastring.split(b"\r\n")
    for item in lines:
        for word in BADLIST:
            if word in item.lower():
                return True
    return False


# check url for skip types jpg, gif, ico and png
def checkskip(url):
    new_url = url.lower()
    for item in SKIPTYPES:
        if new_url.endswith(item):
            return True
    return False


if __name__ == '__main__':
    main()
