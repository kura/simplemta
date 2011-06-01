import sys
import eventlet
import socket
from daemon import Daemon


HOST = "0.0.0.0"
PORT = 25
CONCURRENCY = 10000

def handle(sock, addr):
    fd = sock.makefile('rw')
    fd.write("220 Kura SMTP ready and waiting.\n")
    fd.flush()
    while True:
        line = fd.readline()
        if not line:
            break
        elif line.startswith("HELO"):
            fd.write("250 OK, yo!\n")
        elif line.startswith("MAIL FROM") or line.startswith("RCPT TO"):
            fd.write("250 OK\n")
        elif line.startswith("DATA"):
            handle_data(fd)
            fd.write("250 OK\n")
        elif line.startswith("RSET"):
            fd.write("250 REST\n")
        elif line.startswith("QUIT"):
            fd.write("221 fuck off\n")
            return
        else:
            fd.write("500 wtf?\n")
        fd.flush()

def handle_data(fd):
    fd.write("354 send me data bitch!\n")
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
    d = Daemon("/tmp/ayers-smtpd.pid")
    if sys.argv[1] == "start":
        print "Starting Kura SMTPD..."
        d.start()
    elif sys.argv[1] == "restart":
        print "Restarting Kura SMTPD..."
        eventlet.StopServe()
        d.restart()
    else:
        print "Stopping Kura SMTPD..."
        eventlet.StopServe()
        d.stop()
        sys.exit(0)
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        d.stop()
        sys.exit(0)
