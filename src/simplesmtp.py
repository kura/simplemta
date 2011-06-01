#!/usr/bin/python
import sys
import eventlet
import socket
from daemon import Daemon


#
# I am well aware that this code is very nasty
# but the whole point of this program is a simple
# configurable and easy way of accepting email
# without needing to set-up a real SMTP daemon
# and without all of the disk and system I/O
# for processing.
#


RESPONSES = {
    "RUNNING": "220 SimpleSMTP ready and waiting baby!\n",
    'HELO': "250 OK, yo!\n",
    'MAIL_FROM': "250 OK\n",
    'RCPT_TO': "250 OK\n",
    'DATA': "354 send me data bitch!\n",
    'DOT': "250 OK\n",
    'RSET': "250 RSET\n",
    'QUIT': "221 fuck off!\n",
    'ERROR': "500 wtf?\n",
}

HOST = "0.0.0.0"
PORT = 8098
CONCURRENCY = 10000

def handle(sock, addr):
    fd = sock.makefile('rw')
    fd.write(RESPONSES['RUNNING'])
    fd.flush()
    while True:
        line = fd.readline()
        if not line:
            break
        elif line.startswith("HELO"):
            fd.write(RESPONSES['HELO'])
        elif line.startswith("MAIL FROM"):
            fd.write(RESPONSES['MAIL_FROM'])
        elif line.startswith("RCPT TO"):
            fd.write(RESPONSES['RCPT_TO'])
        elif line.startswith("DATA"):
            handle_data(fd)
            fd.write(RESPONSES['DOT'])
        elif line.startswith("RSET"):
            fd.write(RESPONSES['RSET'])
        elif line.startswith("QUIT"):
            fd.write(RESPONSES['QUIT'])
            return
        else:
            fd.write(RESPONSES['ERROR'])
        fd.flush()

def handle_data(fd):
    fd.write(RESPONSES['DATA'])
    fd.flush()
    while True:
        line = fd.readline()
        if line[0] == "." and len(line) == 3 and ord(line[0]) == 46:
            return
        else:
            fd.write(line)

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
        print "Starting SimpleSMTPD..."
        d.start()
    elif sys.argv[1] == "restart":
        print "Restarting SimpleSMTPD..."
        eventlet.StopServe()
        d.restart()
    else:
        print "Stopping SimpleSMTPD..."
        eventlet.StopServe()
        d.stop()
        sys.exit(0)
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        d.stop()
        sys.exit(0)
