import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import version as python_version
from cgi import parse_header, parse_multipart
from urllib.parse import parse_qs

import json
import cgi

from printer import send_print_job

hostName = "localhost"
serverPort = 8080


class MyServer(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS,POST')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    """
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        path_splited = self.path.split('/')
        printer = path_splited[-2]
        base64data = path_splited[-1]
        print(printer)
        print(base64data)
        send_print_job(printer, base64data)
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))
    """

    # POST echoes the message adding a JSON field
    def do_POST(self):
        print(self.headers)
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))

        # refuse to receive non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return

        # read the message and convert it into a python dictionary
        length = int(self.headers.get('content-length'))
        message = json.loads(self.rfile.read(length))

        path_splited = self.path.split('/')
        printer = path_splited[-2]
        base64data = path_splited[-1]
        print(printer)
        print(base64data)

        base64string = message.get('base64')
        filename = message.get('filename')
        options = {}
        if base64string:
            options['base64'] = base64string
        if filename:
            options['filename'] = filename
        send_print_job(message['printer'], options)

        # add a property to the object, just to mess with data
        message['received'] = 'ok'

        # send the message back
        self._set_headers()
        print(message)

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS,POST')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

        self.send_header('Content-type', 'application/json')
        self.end_headers()


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
