#!/usr/bin/python
import socket
import select
import subprocess
import Queue
from random import randint


def bash_it(cmd):
    process = subprocess.Popen(cmd, shell=True, executable="/bin/bash", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process.communicate()


def elect_leader(votes):
    try:
        rand_idx = randint(0, len(votes) - 1)
        return votes[rand_idx]
    except ValueError or IndexError:
        print("Failed to elect a leader")
        exit()


def main():
    # Get the number of CPU cores
    try:
        num_cores = bash_it("grep -c ^processor /proc/cpuinfo")
        if num_cores[0] == '':
            print("Linux op to get Num Cores failed. Trying MacOS variant...")
            num_cores = int(bash_it("sysctl -n hw.ncpu")[0]) * 2
            if num_cores is None or num_cores < 0:
                print("Cannot dynamically determine CPU cores... setting default to 8.")
                num_cores = 8
    except EnvironmentError:
        print("Cannot dynamically determine CPU cores... setting default to 8.")
        num_cores = 8

    server_address = ('localhost', 11000)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setblocking(0)  # Non-blocking TCP/IP socket
    print('PirateBay server is up on %s port %s' % server_address)
    server_socket.bind(server_address)
    server_socket.listen(num_cores)  # Listen for #num_cores incoming connection
    timeout_seconds = 60
    inputs = [server_socket]  # Sockets from which we expect to read
    outputs = []  # Sockets to which we expect to write
    message_queues = {}  # Outgoing message queues (socket:Queue)
    possible_leader_votes = []
    readable = None
    writable = None
    exceptional = None
    num_connections = 0
    try:
        while num_connections < 3:  # need at least 3 to elect leader
            readable, writable, exceptional = select.select(inputs, outputs, inputs, timeout_seconds)
            for soc in readable:
                if soc is server_socket:
                    connection, client_address = soc.accept()
                    connection.setblocking(0)
                    inputs.append(connection)
                    message_queues[connection] = Queue.Queue()
                    print("New connection from %s:%s" % (client_address[0], str(client_address[1])))
                    num_connections += 1
                    print("Number of connected Pirates: %d" % num_connections)
                    data = connection.recv(1024)  # receive 1024 bytes of data
                    if data:
                        message_queues[connection].put(data)
                        try:
                            pirate_vote = message_queues[connection].get_nowait()
                            possible_leader_votes.append(pirate_vote)
                        except Queue.Empty:
                            print("Unable to retrieve pirate vote.")
                        else:
                            print("Pirate %s voted for %s" % (soc, pirate_vote))
                        if connection not in outputs:
                            outputs.append(connection)
                    else:  # if no data received then remove connection from input and output then close the socket.
                        if connection in outputs:
                            outputs.remove(connection)
                        inputs.remove(connection)
                        connection.close()
                        del message_queues[connection]

            for soc in exceptional:
                inputs.remove(soc)
                if soc in outputs:
                    outputs.remove(soc)
                soc.close()
                del message_queues[soc]
    except EnvironmentError:
        if exceptional:
            for soc in exceptional:
                inputs.remove(soc)
                if soc in outputs:
                    outputs.remove(soc)
                soc.close()
                del message_queues[soc]
        server_socket.close()
    finally:
        leader_pid = elect_leader(possible_leader_votes)
        print("The elected leader pid is %s" % leader_pid)
        for soc in outputs:
            try:
                soc.send(leader_pid)  # send elected leader
            except EnvironmentError:
                print("Failed to send elected leader to pirate on socket %s" % soc)
        server_socket.close()


if __name__ == "__main__":
    main()
