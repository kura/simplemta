#!/usr/bin/python

import sys
import eventlet
import socket
import random
import atexit
import logging
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

# IP to bind to
# default: 0.0.0.0
# all interfaces
HOST = "0.0.0.0"

# Port to bind to
# default: 25
PORT = 25

# Number of concurrent requests to server
# the higher the number the more microthreads
# can be spawned
# default: 10000
CONCURRENCY = 10000

# How to handle in coming mail
# ACCEPT, BOUNCE, RANDOM
# default: ACCEPT
HANDLE = "ACCEPT"  # always accept
#HANDLE = "BOUNCE" # always bounce - random code
#HANDLE = "RANDOM"  # randomise response

# Debugging
# This can really hammer your disk if
# enabled so use with caution.
# Best disabled when stress testing
# default: False
DEBUG = False

# Location to log to
# default: /tmp/simplemta.log
LOG_FILE = "/tmp/simplemta.log"

# Response table
RESPONSES = {
    '220': "220 2.2.0 SimpleMTA ready and waiting baby!\n",
    '221': "221 2.2.1 fuck off!\n",
    '250': "250 2.5.0 OK, yo!\n",
    '354': "354 3.5.4 send me data bitch!\n",
    '421': "421 4.2.1 uh shit... I don't work\n",
    '422': "422 4.2.2 full, argh\n",
    '431': "431 4.3.1 out of diskies\n",
    "432": "432 4.3.2 frozen\n",
    '450': "450 4.5.0 I couldn't do it =(\n",
    '451': "451 4.5.1 abort abort abort\n",
    '452': "452 4.5.2 no space dude\n",
    '500': "500 5.0.0 wtf?\n",
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


# Successful response: 250
# Random responses
RANDOM_RESPONSES = ('250', '421', '422', '431', '432', '450', '451', '452', '515', '521', '522',
                    '523', '531', '533', '534', '547', '550', '551', '552', '553', '554', '571')
# Bounce responses
BOUNCE_RESPONSES = ('421', '422', '431', '432', '450', '451', '452', '515', '521', '522', '523',
                    '531', '533', '534', '547', '550', '551', '552', '553', '554', '571')

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s %(message)s"

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
formatter = logging.Formatter(LOGGING_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.INFO)
stream.setFormatter(logging.Formatter("%(message)s"))

file_log = logging.FileHandler(LOG_FILE)
file_log.setLevel(logging.DEBUG)
file_log.setFormatter(formatter)

log.addHandler(stream)
log.addHandler(file_log)

def handle(sock, addr):
    """
    Main worker, called on each new connection
    as a microthread.
    Loops over incoming mail data
    """
    fd = sock.makefile('rw')
    resp = RESPONSES['220']
    fd.write(resp)
    fd.flush()
    if DEBUG is True:
        log.debug("Connect from: %s" % addr[0])
        log.debug(resp.strip("\n"))
    while True:
        line = fd.readline()
        resp = ""
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
        if DEBUG is True:
            log.debug(line.strip("\n"))
            log.debug(resp.strip("\n"))
        fd.write(resp)
        fd.flush()

def handle_data(fd):
    """
    Worker to handle data sent after DATA
    command is received.
    Loops waiting for \n.\n
    """
    resp = RESPONSES['354']
    fd.write(resp)
    if DEBUG is True:
        log.debug(resp.strip("\n"))
    fd.flush()
    while True:
        line = fd.readline()
        if DEBUG is True:
            log.debug(line.strip("\n"))
        if line[0] == "." and len(line) == 3 and ord(line[0]) == 46:
            return

def handle_complete(fd):
    """
    Worker to handle the returned response
    code.
    Code returned is based on HANDLE variable
    """
    if HANDLE == "ACCEPT":
        resp = RESPONSES['250']
    elif HANDLE == "BOUNCE":
        rand = random.randrange(0, len(BOUNCE_RESPONSES))
        resp = BOUNCE_RESPONSES[rand]
        resp = RESPONSES[resp]
    elif HANDLE == "RANDOM":
        rand = random.randrange(0, len(RANDOM_RESPONSES))
        resp = RANDOM_RESPONSES[rand]
        resp = RESPONSES[resp]
    if DEBUG is True:
        log.debug(resp.strip("\n"))
    fd.write(resp)
    return

def main():
    """
    Spawns the listener
    """
    try:
        eventlet.serve(eventlet.listen((HOST, PORT)), handle, concurrency=CONCURRENCY)
    except socket.error as e:
        log.warn(e)
        eventlet.StopServe()
        sys.exit(0)

if __name__ == "__main__":
    d = Daemon("/tmp/simplesmtpd.pid")
    if sys.argv[1] == "start":
        log.info("Starting SimpleMTA %s:%s..." % (HOST, PORT))
        d.start()
    elif sys.argv[1] == "restart":
        log.info("Restarting SimpleMTA %s:%s..." % (HOST, PORT))
        eventlet.StopServe()
        d.restart()
    else:
        log.warn("Stopping SimpleMTA...")
        eventlet.StopServe()
        d.stop()
        sys.exit(0)
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        log.info("Stopping SimpleMTA...")
        eventlet.StopServe()
        d.stop()
        sys.exit(0)
