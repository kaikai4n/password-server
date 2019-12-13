import argparse
import hashlib
import os
import posixpath
import random
import string
import urllib
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from http.server import test


def gen_password(stringLength=8):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits)
                   for i in range(stringLength))


def hash_password(password):
    m = hashlib.sha256()
    m.update(password.encode('utf-8'))
    password = m.digest()
    return password


class VerifyHTTPServer(HTTPServer):
    """Verify client section codes"""

    MAX_LOGIN_ATTEMPTS = 3

    def __init__(self, *args):
        self.password
        super().__init__(*args)

    def verify_request(self, request, client_address):
        if client_address[0] in self.not_verified_clients and \
            self.not_verified_clients[client_address[0]] >= \
                self.MAX_LOGIN_ATTEMPTS:
            return False
        return True

    @property
    def password(self):
        if not hasattr(self, '_password'):
            password = gen_password()
            print(f'password is {password}')
            self._password = hash_password(password)
        return self._password

    @property
    def verified_clients(self):
        if not hasattr(self, '_verified_clients'):
            self._verified_clients = set()
        return self._verified_clients

    def add_verified_clients(self, client):
        self._verified_clients.add(client)

    @property
    def not_verified_clients(self):
        if not hasattr(self, '_not_verified_clients'):
            self._not_verified_clients = {}
        return self._not_verified_clients

    def add_not_verified_clients(self, client):
        if client not in self._not_verified_clients:
            self._not_verified_clients[client] = 0
        self._not_verified_clients[client] += 1


class MySimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.client_address[0] in self.server.verified_clients:
            super().do_GET()
        else:
            password = self.path.lstrip('/')
            if hash_password(password) == self.server.password:
                print(f'Verified client {self.client_address[0]}')
                self.server.add_verified_clients(self.client_address[0])
                self.path = '/'
                super().do_GET()
            else:
                self.server.add_not_verified_clients(self.client_address[0])
                print(f'Not verified client {self.client_address[0]}'
                      f' with password {password}')

    def do_HEAD(self):
        raise Exception('Code should not be here')
        if self.client_address in self.server.verified_clients:
            super().do_HEAD()

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        try:
            path = urllib.parse.unquote(path, errors='surrogatepass')
        except UnicodeDecodeError:
            path = urllib.parse.unquote(path)
        path = posixpath.normpath(path)
        words = path.split('/')
        words = filter(None, words)
        global root_dir
        path = root_dir
        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', '-b', default='', metavar='ADDRESS',
                        help='Specify alternate bind address '
                             '[default: all interfaces]')
    parser.add_argument('port', action='store',
                        default=8000, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8000]')
    parser.add_argument('--dir', required=True,
                        help='The directory wants to show.'
                             'It may be unsafe to show the source code '
                             'of this server.')
    args = parser.parse_args()
    global root_dir
    root_dir = os.path.abspath(args.dir)
    handler_class = MySimpleHTTPRequestHandler
    test(
        HandlerClass=handler_class,
        ServerClass=VerifyHTTPServer,
        port=args.port,
        bind=args.bind
    )
