#!/usr/bin/env python3

# See https://docs.python.org/3.2/library/socket.html
# for a description of python socket and its parameters
#
# Copyright 2018, Shaden Smith, Koorosh Vaziri,
# Niranjan Tulajapure, Ambuj Nayab, Akash Kulkarni, and Daniel J. Challou
# for use by students enrolled in Csci 4131 at the University of
# Minnesota-Twin Cities only. Do not reuse or redistribute further
# without the express written consent of the authors.
#
import socket

#add the following
import socket
import os
import stat
import sys
import urllib.parse
import datetime
import base64
from urllib.parse import urlparse

from threading import Thread
from argparse import ArgumentParser



BUFSIZE = 4096
#add the following
CRLF = '\r\n'
METHOD_NOT_ALLOWED = 'HTTP/1.1 405  METHOD NOT ALLOWED{}Allow: GET, HEAD{}Connection: close{}{}'.format(CRLF, CRLF, CRLF, CRLF)
OK = 'HTTP/1.1 200 OK{}{}{}'.format(CRLF, CRLF, CRLF)
DELETE_OK = 'HTTP/1.1 200 OK{}'.format(CRLF)
NOT_FOUND = 'HTTP/1.1 404 NOT FOUND{}Connection: close{}{}'.format(CRLF, CRLF, CRLF)
FORBIDDEN = 'HTTP/1.1 403 FORBIDDEN{}Connection: close{}{}'.format(CRLF, CRLF, CRLF)
MOVED_PERMANENTLY = 'HTTP/1.1 301 MOVED PERMANENTLY{}Location:  https://www.cs.umn.edu/{}Connection: close{}{}'.format(CRLF, CRLF, CRLF, CRLF)
CREATED = 'HTTP/1.1 201 Created{}Content-Location: '.format(CRLF)
REPLACED = 'HTTP/1.1 200 OK{}Content-Location: '.format(CRLF)
END = '{}Connection: close{}{}'.format(CRLF, CRLF, CRLF)
GENERAL_ALLOW = 'Allow: OPTIONS, GET, HEAD, POST, PUT, DELETE{}'.format(CRLF)
CAL_ALLOW = 'Allow: OPTIONS, GET, HEAD{}'.format(CRLF)
ALLOW = 'Allow: OPTIONS, GET, HEAD, POST{}'.format(CRLF)
CACHE_CONTROL = 'Cache-Control: max-age=604800{}'.format(CRLF)
DATE = 'Date: ' + str(datetime.datetime.now()) + '{}'.format(CRLF)
CONTENT_LENGTH = 'Content-Length: 0{}'.format(CRLF)
NOT_ACCEPTABLE = 'HTTP/1.1 406 Not Acceptable{}{}{}'.format(CRLF,CRLF,CRLF)
# def get_contents(fname):
#     with open(fname, 'r') as f:
#         return f.read()
#

def check_perms(resource):
    """Returns True if resource has read permissions set on 'others'"""
    stmode = os.stat(resource).st_mode
    return (getattr(stat, 'S_IROTH') & stmode) > 0


def client_talk(client_sock, client_addr):
    print('talking to {}'.format(client_addr))
    data = client_sock.recv(BUFSIZE)
    while data:
      print(data.decode('utf-8'))
      data = client_sock.recv(BUFSIZE)

    # clean up
    client_sock.shutdown(1)
    client_sock.close()
    print('connection closed.')

class HTTP_HeadServer:  #A re-worked version of EchoServer
    def __init__(self, host, port):
        print('listening on port {}'.format(port))
        self.host = host
        self.port = port

        self.setup_socket()

        self.accept()

        self.sock.shutdown()
        self.sock.close()

    def setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(128)

    def accept(self):
        while True:
          (client, address) = self.sock.accept()
          #th = Thread(target=client_talk, args=(client, address))
          try:
              th = Thread(target=self.accept_request, args=(client, address))
              th.start()
          except:
              sock.close()
              ("\nClosed Port\n")

    # here, we add a function belonging to the class to accept
    # and process a request
    def accept_request(self, client_sock, client_addr):
        print("accept request")
        data = client_sock.recv(BUFSIZE)
        req = data.decode('utf-8') #returns a string
        print("REQUEST: "+req)

        response=self.process_request(req)

        #once we get a response, we chop it into utf encoded bytes
        #and send it (like EchoClient)
        #print("sending response" + response)
        client_sock.send(bytes(response,'utf-8'))

        #clean up the connection to the client
        #but leave the server socket for recieving requests open
        client_sock.shutdown(1)
        client_sock.close()

    # here we process our requests, send any given request to it's proper handler
    # and return the response message to the accept_requests method
    def process_request(self, request):
        print('######\nREQUEST:\n{}######'.format(request))
        linelist = request.strip().split(CRLF)
        reqline = linelist[0]

        rlwords = reqline.split()
        if len(rlwords) == 0:
            return ''
        if rlwords[0] == 'HEAD':
            resource = rlwords[1][1:] # skip beginning /
            return self.head_request(linelist, resource)
        elif rlwords[0] == 'GET':
            resource = rlwords[1][1:] # skip beginning /
            return self.get_request(linelist, resource)
        elif rlwords[0] == 'PUT':
            resource = rlwords[1][1:] # skip beginning /
            return self.handle_put(linelist, resource)
        elif rlwords[0] == 'POST':
            resource = rlwords[1][1:] # skip beginning /
            return self.handle_post(linelist, resource)
        elif rlwords[0] == 'DELETE':
             resource = rlwords[1][1:] # skip beginning /
             return self.delete_request(resource)
        elif rlwords[0] == 'OPTIONS':
             resource = rlwords[1][1:] # skip beginning /
             return self.options_request(resource)
        else:
            return METHOD_NOT_ALLOWED

    # In this method we handle a HEAD request
    def head_request(self, linelist, resource):
        """Handles HEAD requests."""
        path = os.path.join('.', resource) #look in directory where server is running
        if resource == 'csumn':
          ret = MOVED_PERMANENTLY
        elif not os.path.exists(resource):
          ret = NOT_FOUND
        elif not check_perms(resource):
          ret = FORBIDDEN
        elif self.acceptsTypeProper(linelist, resource):
          ret = OK
        else:
            ret = NOT_ACCEPTABLE
        return ret

    # In this method we check if there is an accept header and if there is
    # we verify that the resource the client specified matches the accept header
    # mimetype, return true if the resource is compatible with the accept header
    # or if there is no accept header
    def acceptsTypeProper(self, linelist, resource):
        #print("Looking for proper accept type")
        acceptTypeFound = False
        acceptTypeSameAsResource = False
        acceptsArray = []
        it = 0
        for lin in linelist:
            #print(it," ", lin, "\n")
            it+=1
            if "Accept:" in lin:
                body = lin.split(" ")
                acceptsArray = body[1]
                acceptTypeFound = True
        if not acceptTypeFound:
            return True
        else:
            resourceArr = resource.split(".")
            if len(resourceArr) == 1:
                return True
            end = resourceArr[len(resourceArr)-1]
            acceptsContainingArray = acceptsArray.split(",")
            acceptable = False
            # loop through accept accept array
            for accepts in acceptsContainingArray:
                formatted_accept = accepts.replace(',', '')
                splits = formatted_accept.split('/')
                mimeType = splits[len(splits)-1]
                #print(mimeType)
                if mimeType.lower() == end.lower():
                    acceptable = True

            return acceptable

    # Handles GET requests
    def get_request(self, linelist, resource):
            """Handles GET requests."""
            #print("handling GET request\n")
            path = os.path.join('.', resource) #look in directory where server is running
            if resource == 'csumn':
              ret = MOVED_PERMANENTLY
            elif not os.path.exists(resource):
              ret = NOT_FOUND + self.get404()
            elif not check_perms(resource):
              ret = FORBIDDEN + self.get403()
            elif self.acceptsTypeProper(linelist, resource):
              ret = OK + self.getFile(resource)
            else:
                ret = NOT_ACCEPTABLE + self.get406()
            return ret


    # Handles PUT requests, creates the resource
    def handle_put(self, linelist, resource):
        """Handles PUT requests."""
        found = os.path.exists(resource)
        it = 0
        content_length = ""
        content_type = ""
        last_line =""

        split_resource = resource.split(".")
        last_line = linelist[len(linelist)-1]
        url = resource
        f = open(url,'w+')
        f.write(last_line)
        f.close()

        if found:
            return REPLACED + url + END
        else:
            return CREATED + url + END

    # Handles POST requests, returns html code that will send back the form data
    # that was attempting to be posted
    def handle_post(self, linelist, resource):
        """Handles POST requests."""
        #print("handling post")
        found = os.path.exists(resource)
        it = 0
        content_length = ""
        content_type = ""
        last_line =""
        for lin in linelist:
            #print(it," ", lin, "\n")
            it+=1
            if "Content-Length" in lin:
                body = lin.split(" ")
                content_length = body[1]
            elif "Content-Type" in lin:
                body = lin.split("/")
                content_type = body[1]
            last_line = lin
        response = OK + "<div> Following Form Data Submitted Successfully </div>"
        #if content_type == "x-www-form-urlencoded":
        query_dict = urllib.parse.parse_qs(last_line)
        for key, value in query_dict.items():
             #print(key, value[0])
             response = response + "<div>" + key + ": " + value[0] + "<div>"
        response = response + "</body></html>"
        return response

    # This method handles the delete request
    def delete_request(self, resource):
        """Handles DELETE requests."""
        path = os.path.join('.', resource) #look in directory where server is running
        if resource == 'csumn':
            ret = MOVED_PERMANENTLY
        elif not os.path.exists(resource):
            ret = NOT_FOUND + get_contents('404.html')
        elif not check_perms(resource):
            ret = FORBIDDEN + get_contents('403.html')
        else:
            ret = DELETE_OK + self.deleteFile(resource)
        return ret

    # Helper for the delete handler, actually deletes the file
    def deleteFile(self, resource):
        os.remove(resource)
        now = datetime.datetime.now()
        return str(now)

    # Handler for options requests
    def options_request(self, resource):
      """Handles OPTIONS requests."""
      path = os.path.join('.', resource) #look in directory where server is running
      message = ''
      if resource == '':
          message += OK + GENERAL_ALLOW + CACHE_CONTROL + DATE + CONTENT_LENGTH
      elif resource == 'calendar.html':
          message += OK + CAL_ALLOW + CACHE_CONTROL + DATE + CONTENT_LENGTH
      elif resource == 'form.html':
          message += OK + ALLOW + CACHE_CONTROL + DATE + CONTENT_LENGTH
      return message

     # return 404, 403 and 406 messages
    def get404(self):
        path = "./404.html"
        f = open(path,'r')
        message = f.read()
        f.close()
        #print("404 message :"+message)
        return message

    def get406(self):
        path = "./406.html"
        f = open(path,'r')
        message = f.read()
        f.close()
        return message


    def get403(self):
        path = "./403.html"
        f = open(path,'r')
        message = f.read()
        f.close()
        #print("403 message :"+message)
        return message

    # gets the contents of a file
    def getFile(self, resource):
        if resource.endswith(".jpeg") or resource.endswith('.png'):
            with open(resource, 'rb') as fp:
                message = base64.b64encode(fp.read())
            return message.decode()
        else:
            f = open(resource,'r')
            message = f.read()
            f.close()
            return message


#to do a get request, read resource contents and append to ret value.
#(you should check types of accept lines before doing so)
def parse_args():
  parser = ArgumentParser()
  parser.add_argument('--host', type=str, default='localhost',
                      help='specify a host to operate on (default: localhost)')
  parser.add_argument('-p', '--port', type=int, default=9001,
                      help='specify a port to operate on (default: 9001)')
  args = parser.parse_args()
  return (args.host, args.port)


if __name__ == '__main__':
  (host, port) = parse_args()
  HTTP_HeadServer(host, port) #Formerly EchoServer
