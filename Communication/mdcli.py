import sys
from mdcliapi import MajorDomoClient

def main():
    verbose = '-v' in sys.argv
    client = MajorDomoClient("tcp://localhost:5555", verbose)
    requests = 100000
    for i in range(requests):
        request = b"Hello world"
        try:
            client.send(b"echo", request)
        except KeyboardInterrupt:
            print("send interrupted, aborting")
            return

    count = 0
    while count < requests:
        try:
            reply = client.recv()
        except KeyboardInterrupt:
            break
        else:
            # also break on failure to reply:
            if reply is None:
                break
        count += 1
    print("%i requests/replies processed" % count)

if __name__ == '__main__':
    main()