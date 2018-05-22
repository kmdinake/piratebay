#!/usr/bin/python
import os
import json
import socket
import select
import subprocess
import Queue
from hashlib import md5


def bash_it(args):
    cmd = "python ../Rummy_src/rummy.pyc " + args
    process = subprocess.Popen(cmd, shell=True, executable="/bin/bash", stdout=subprocess.PIPE)
    return process.communicate()


def wake():
    print(json.loads(bash_it("-wake")[0])['message'])


def gather():
    print(json.loads(bash_it("-gather")[0])['message'])


def unlock():
    print(json.loads(bash_it("-unlock")[0])['message'])


def prepare():
    print(json.loads(bash_it("-prepare")[0])['message'])


def add(size):
    print("Add %d crew members..." % size)
    return json.loads(bash_it("-add " + str(size))[0])


def ship_out():
    print("Shipping out...")
    print(json.loads(bash_it("-shipout")[0])['message'])


def clues():
    print("Getting clues...")
    return json.loads(bash_it("-clues")[0])


def verify(keys):
    payload = '{"id":"PirateID", "data":[{"id":"ClueID", "key":"ClueKey"}]}'
    # return json.loads(bash_it("-verify " + keys)[0])


class Pirate(object):
    def __init__(self):
        self.__pirate_id = None
        self.__is_quarter_master = False

    def set_pirate_id(self, pid):
        self.__pirate_id = pid

    def get_pirate_id(self):
        return self.__pirate_id

    def set_is_quarter_master(self, is_qm):
        self.__is_quarter_master = is_qm

    def get_is_quarter_master(self):
        return self.__is_quarter_master

    def __dig_in_the_sand(self, clue):
        if clue is None:
            return []
        for i in range(100):
            clue = self.__shovel(clue)
        for i in range(200):
            clue = self.__bucket(clue)
        for i in range(100):
            clue = self.__shovel(clue)
        return clue

    def __search_the_river(self, clue):
        if clue is None:
            return []
        for i in range(200):
            clue = self.__bucket(clue)
        return clue

    def __crawl_into_the_cave(self, clue):
        if clue is None:
            return []
        for i in range(200):
            clue = self.__rope(clue)
        for i in range(100):
            clue = self.__torch(clue)
        return clue

    def solve_the_clue(self, clue):
        clue = self.__dig_in_the_sand(clue)
        clue = self.__search_the_river(clue)
        clue = self.__crawl_into_the_cave(clue)
        clue = self.chr_list_to_str(clue)
        key = md5(clue).hexdigest()
        return key.upper()

    def __shovel(self, clue):
        clue = self.__sort(clue)
        if clue is not None and clue[0].isdigit():
            rand_str = ['0', 'A', '2', 'B', '3', 'C']
            clue += rand_str
        else:
            rand_str = ['1', 'B', '2', 'C', '3', 'D']
            clue += rand_str
        clue = clue[1:]
        return clue

    @staticmethod
    def __rope(clue):
        if clue is None:
            return []
        for x in range(len(clue)):
            if clue[x].isdigit():
                mod = int(clue[x]) % 3
                if mod == 0:
                    clue[x] = "5"
                elif mod == 1:
                    clue[x] = "A"
                elif mod == 2:
                    clue[x] = "B"
            elif clue[x].isalpha():
                hex_clue_x = int(clue[x], 16) - 10
                mod = hex_clue_x % 5
                if mod == 0:
                    clue[x] = "C"
                elif mod == 1:
                    clue[x] = "1"
                elif mod == 2:
                    clue[x] = "2"
        return clue

    @staticmethod
    def __torch(clue):
        if clue is None:
            return []
        clue_digits = filter(lambda c: c.isdigit(), clue)
        x = 0
        for it in clue_digits:
            x += int(it)
        if x < 100:
            x *= x
        str_x = str(x)
        if len(str_x) < 10:
            return "F9E8D7" + str_x[1:]
        else:
            return str_x[6:] + "A1B2C3"

    def __bucket(self, clue):
        if clue is None:
            return []
        for x in range(len(clue)):
            if clue[x].isdigit():
                x_int = int(clue[x])
                if x_int > 5:
                    clue[x] = str(x_int - 2)
                else:
                    clue[x] = str(x_int * 2)
        clue = self.chr_list_to_str(clue)
        clue = self.str_to_chr_list(clue)
        return clue

    @staticmethod
    def __sort(clue):
        if clue is None:
            return []
        digits = sorted(filter(lambda c: c.isdigit(), clue))
        if digits is None:
            digits = []
        alphas = sorted(filter(lambda c: c.isalpha(), clue))
        if alphas is None:
            alphas = []
        sorted_clue = digits + alphas
        return sorted_clue

    @staticmethod
    def str_to_chr_list(clue):
        chr_list = list()
        for x in range(len(clue)):
            chr_list.append(clue[x])
        return chr_list

    @staticmethod
    def chr_list_to_str(clue):
        str_clue = ""
        for c in clue:
            str_clue += c
        return str_clue


def elect_self_as_quarter_master(soc, pid):
    data = -1  # select self by default
    try:
        print("Voting %d for Quarter Master..." % pid)
        soc.connect(('localhost', 11000))
        soc.sendall(str(pid))
        data = soc.recv(1024)
        print('Elected Quarter Master pid %s' % str(data))
    except EnvironmentError:
        print("Failed to connect to the PirateBay server.")
    finally:
        soc.close()
    if data != '' and data is not None:
        return int(data)
    else:
        return -1


def get_clue():
    return "40938FC0CB3F48B98C7546AD05CC7434"


def send_key(key):
    pass


def main():
    clues_received = list()
    clues_solved = list()
    possible_keys = list()
    quarter_master_id = None
    crew = list()

    print("Pirate process %d is running" % (os.getpid()))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pirate = Pirate()
    quarter_master_id = elect_self_as_quarter_master(client_socket, os.getpid())
    if quarter_master_id is os.getpid() or quarter_master_id == os.getpid():
        client_socket.close()
        pirate.set_is_quarter_master(is_qm=True)
        server_address = ('localhost', 12000)
        quarter_master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        quarter_master_socket.setblocking(0)  # Non-blocking TCP/IP socket
        print('Quarter Master is up on %s port %s' % server_address)
        quarter_master_socket.bind(server_address)
        quarter_master_socket.listen(8)  # listen to up to 8 connections
        inputs = [quarter_master_socket]
        outputs = []
        message_queues = {}
        exit_condition = True
        unlock()
        payload = add(8)
        if payload is not None and payload['status'] != "error":
            crew = payload['data']
        ship_out()
        payload = clues()
        if payload is not None and payload['status'] != "error":
            clues_received = payload['data']
        num_connections = 0
        readable = None
        writable = None
        exceptional = None
        num_connections = 0
        # Accept pirate connections
        try:
            print("Registering Pirates...")
            while num_connections < 4:
                readable, writable, exceptional = select.select(inputs, outputs, inputs, 60)
                for soc in readable:
                    if soc is quarter_master_socket:
                        connection, client_address = soc.accept()
                        connection.setblocking(0)
                        inputs.append(connection)
                        message_queues[connection] = Queue.Queue()
                        print("New connection from %s:%s" % (client_address[0], str(client_address[1])))
                        num_connections += 1
                        print("Number of connected Pirates: %d" % num_connections)
                        message_queues[connection].put((crew[num_connections - 1], clues_received))
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
            quarter_master_socket.close()
        finally:
            print("Sending clues to Pirates...")
            for soc in outputs:
                try:
                    payload = message_queues[soc].get_nowait()
                except Queue.Empty:
                    print("Failed to send payload to pirate on socket %s" % soc)
                else:
                    soc.send(payload)  # send pirate id and clues

    # verify clues

    elif quarter_master_id == -1:
        exit()
    else:
        exit_condition = True
        while exit_condition:
            print("Do crew member duties")
            clue = get_clue()
            key = pirate.solve_the_clue(clue=pirate.str_to_chr_list(clue))
            send_key(key)
    print("My work here is done.")


if __name__ == '__main__':
    main()

