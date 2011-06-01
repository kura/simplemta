#!/usr/bin/python

import sys
import eventlet
import socket
import random
from daemon import Daemon


__author__ = "Kura"
__copyright__ = "None"
__credits__ = ["Kura", "Richard Noble"]
__license__ = "BSD 3-Clause"
__version__ = "0.1"
__maintainer__ = "Kura"
__email__ = "kura@deviling.net"
__status__ = "Development"


#
# I am well aware that this code is very nasty
# but the whole point of this program is a simple
# configurable and easy way of accepting email
# without needing to set-up a real SMTP daemon
# and without all of the disk and system I/O
# for processing.
#

HOST = "0.0.0.0"
PORT = 25
CONCURRENCY = 10000
ALWAYS_ACCEPT = False
ALWAYS_BOUNCE = False
ALWAYS_RANDOM = True

RESPONSES = {
    "220": "220 2.2.0 Simple(E)SMTP ready and waiting baby!\n",
    '250': "250 2.5.0 OK, yo!\n",
    '354': "354 3.5.4 send me data bitch!\n",
    '221': "221 2.2.1 fuck off!\n",
    '500': "500 5.0.0 wtf?\n",
    '421': "421 4.2.1 uh shit... I don't work\n",
    '422': "422 4.2.2 full, argh\n",
    '431': "431 4.3.1 out of diskies\n",
    "432": "432 4.3.2 frozen\n",
    '450': "450 4.5.0 I couldn't do it =(\n",
    '451': "451 4.5.1 abort abort abort\n",
    '452': "452 4.5.2 no space dude\n",
    '501': "501 5.0.1 wrong syntax noob\n",
    '502': "502 5.0.2 I'm too stupid to know that command\n",
    '503': "503 5.0.3 incorrect order, does not compute\n",
    '515': "515 5.1.5 invalid mailbox\n",
    '521': "521 5.2.1 message too fucking big\n",
    '522': "522 5.2.2 this bitch has used all her capacity\n",
    '523': "523 5.2.3 this is too big for this recipient\n",
    '531': "531 5.3.1 mail system is full, apparently\n",
    '533': "533 5.3.3 out of disk\n",
    '534': "534 5.3.4 message too big\n",
    '547': "547 5.4.7 delivery time-out\n",
    '550': "550 5.5.0 I just can't do it captain, I don't have the power\n",
    '551': "551 5.5.1 user isn't from around here, you need <>\n",
    '552': "552 5.5.2 out of space\n",
    '553': "553 5.5.3 invalid shit\n",
    '554': "554 5.5.4 transaction failed\n",
    '571': "571 5.7.1 you're blocked by this user. ha\n",
}

RANDOM_RESPONSES = ('250', '421', '422', '431', '432', '450', '451', '452', '515', '521', '522',
                    '523', '531', '533', '534', '547', '550', '551', '552', '553', '554', '571')
BOUNCE_RESPONSES = ('421', '422', '431', '432', '450', '451', '452', '515', '521', '522', '523',
                    '531', '533', '534', '547', '550', '551', '552', '553', '554', '571')

def handle(sock, addr):
    fd = sock.makefile('rw')
    fd.write(RESPONSES['220'])
    fd.flush()
    while True:
        line = fd.readline()
        if not line:
            break
        elif line.startswith("HELO"):
            resp = RESPONSES['250']
        elif line.startswith("EHLO"):
            resp = RESPONSES['250']
        elif line.startswith("MAIL FROM"):
            resp = RESPONSES['250']
        elif line.startswith("RCPT TO"):
            resp = RESPONSES['250']
        elif line.startswith("DATA"):
            handle_data(fd)
            handle_complete(fd)
        elif line.startswith("RSET"):
            resp = RESPONSES['250']
        elif line.startswith("QUIT"):
            resp = RESPONSES['221']
            return
        else:
            resp = RESPONSES['500']
        fd.write(resp)
        fd.flush()

def handle_data(fd):
    fd.write(RESPONSES['354'])
    fd.flush()
    while True:
        line = fd.readline()
        if line[0] == "." and len(line) == 3 and ord(line[0]) == 46:
            return

def handle_complete(fd):
    if ALWAYS_ACCEPT is True:
        fd.write(RESPONSES['250'])
    elif ALWAYS_BOUNCE is True:
        rand = random.randrange(0, len(BOUNCE_RESPONSES))
        resp = BOUNCE_RESPONSES[rand]
        fd.write(RESPONSES[resp])
    elif ALWAYS_RANDOM is True:
        rand = random.randrange(0, len(RANDOM_RESPONSES))
        resp = RANDOM_RESPONSES[rand]
        fd.write(RESPONSES[resp])
    else:
        fd.write(RESPONSES['250'])
    return

def main():
    try:
        eventlet.serve(eventlet.listen((HOST, PORT)), handle, concurrency=CONCURRENCY)
    except socket.error as e:
        print e
        eventlet.StopServe()
        sys.exit(0)

if __name__ == "__main__":
    d = Daemon("/tmp/simplesmtpd.pid")
    if sys.argv[1] == "start":
        print "Starting Simple(E)SMTPD %s:%s..." % (HOST, PORT)
        d.start()
    elif sys.argv[1] == "restart":
        print "Restarting Simple(E)SMTPD %s:%s..." % (HOST, PORT)
        eventlet.StopServe()
        d.restart()
    else:
        print "Stopping Simple(E)SMTPD..."
        eventlet.StopServe()
        d.stop()
        sys.exit(0)
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        eventlet.StopServe()
        d.stop()
        sys.exit(0)
