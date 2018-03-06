# Project

To better understand HTTP, I've implemented a subset of the HTTP protocol, namely the the GET, POST, PUT, DELETE, and OPTIONS methods. 

# Implementation

Server was implemented in python3
Run the following commands to change permissions for testing purposes
chmod 640 private.html
chmod 644 403.html
chmod 644 404.html
chmod 644 calendar.html 

Run the python server, then go to any client including CURL, POSTMAN, or a web browser and type in http://localhost:9001/calendar.html to send a GET request, testing the other requests will have to be done using CURL or POSTMAN, the server is fairly robust and can send 403-forbidden, 404-not_found, 405-method_not_allowed and 406-not_acceptable error pages when appropriate. To test 403, try and access the file private.html which you made read and write (owner only) in the commands above. To test 406, simply send a request for the calendar.html page while specifying only another file type as accessible.
