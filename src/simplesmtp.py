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
    "220": "220 SimpleSMTP ready and waiting baby!\n",
    '250': "250 OK, yo!\n",
    '354': "354 send me data bitch!\n",
    '221': "221 fuck off!\n",
    '500': "500 wtf?\n",
    '421': "421 uh shit... I don't work\n",
    '450': "450 I couldn't do it =(\n",
    '451': "451 abort abort abort\n",
    '501': "501 wrong syntax noob\n",
    '502': "502 I'm too stupid to know that command\n",
    '503': "503 incorrect order, does not compute\n",
    '550': "550 I just can't do it captain, I don't have the power\n",
    '551': "551 user isn't from around here, you need <>\n",
    '552': "552 out of space\n",
    '553': "553 invalid shit\n",
    '554': "554 transaction failed\n",
}

HOST = "0.0.0.0"
PORT = 25
CONCURRENCY = 10000

def handle(sock, addr):
    fd = sock.makefile('rw')
    fd.write(RESPONSES['220'])
    fd.flush()
    while True:
        line = fd.readline()
        if not line:
            break
        elif line.startswith("HELO"):
            fd.write(RESPONSES['250'])
        elif line.startswith("MAIL FROM"):
            fd.write(RESPONSES['250'])
        elif line.startswith("RCPT TO"):
            fd.write(RESPONSES['250'])
        elif line.startswith("DATA"):
            handle_data(fd)
            fd.write(RESPONSES['250'])
        elif line.startswith("RSET"):
            fd.write(RESPONSES['250'])
        elif line.startswith("QUIT"):
            fd.write(RESPONSES['221'])
            return
        else:
            fd.write(RESPONSES['500'])
        fd.flush()

def handle_data(fd):
    fd.write(RESPONSES['354'])
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
