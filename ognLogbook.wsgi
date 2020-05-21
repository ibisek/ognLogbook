#!/usr/bin/env python

from index import app as application

#
# Below for testing only
#
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('0.0.0.0', 8000, application)
    httpd.serve_forever()
