#!/usr/local/bin/python2.7
# encoding: utf-8

import socket
import sys
import os
import mmap
import json
import datetime
import math
import pymysql
import multiprocessing
import exceptions
import string
import array
import random
import threading
import traceback
import cmd
#from pyamf import remoting

shutdown = False

class TerminalNode(object):
    name = ''
    posx = 0
    posy = 0
    posz = 0
    inventory = []
    players = []
    
    def run(self):
        self.host = 'IP_ADDRESS'
        self.port = 9997
        log('Server started')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.port))
        self.sock.listen(3)
        try:
            while True:
                if shutdown == True:
                    self.sock.shutdown(1)
                    self.sock.close()
                    break
                self.socket = self.sock.accept()
                p = multiprocessing.Process(target=self.handle, args=(self.socket[0],self. socket[1], self.players))
                p.start()
        except socket.error, e:
            log( 'Error accepting connection: %s' % e[1])
    def handle(self, conn, addr, players):
        self.db = pymysql.connect(host='MYSQL_HOST', user='MYSQL_USERNAME', passwd='MYSQL_PASSWORD', db='MYSQL_DATABASE')
        addrstr = '%s:%s' % (addr[0],addr[1])
        try:
            log( 'Connection opened: %s' % addrstr)
            #with contextlib.closing(conn):
            while True:
                # It's possible that we won't get the entire request in
                # a single recv, but very unlikely.
                data = conn.recv(2048)
                if data == '':
                    self.db.close();
                    log('Connection closed: %s' % addrstr)
                    break
                if '\n' in data:
                    log('break found')
                dataList = data.split("%")
                if len(dataList) > 2:
                    action = str(dataList[0])
                    # 0 = no encoding, 1 = json without keys, 2 = json with keys
                    encoding = int(dataList[1])
                    data = dataList[2]
                    log( 'recieved: '+action+' from '+str(addr)+' with data '+data )
                    pdata = self.decode(encoding,data)
                    # Virtal Player Interface
                    if action == 'join':
                        self.join(encoding, pdata, conn, addr)
                    if action == 'move':
                        self.move(encoding, pdata, conn, addr)
                    if action == 'look':
                        self.look(encoding, pdata, conn, addr)
                    if action == 'say':
                        self.say(encoding, pdata, conn, addr)
                    if action == 'grab':
                        self.grab(encoding, pdata, conn, addr)
                        
        except socket.error, e:
            log( 'Error handling connection from %s: %s' % (addrstr, e))
        except Exception, e:
            log('Error handling connection from %s: %s' % (addrstr, e))
    # method to encode and send data
    def sendData(self, encoding, action, pdata, conn, addr):
        message = self.encode(encoding, pdata)
        tosend = action+'%'+str(encoding)+'%'+str(message)+'%;'
        if len(str(message)) > 100:
            log('SENDING: '+action+'%'+str(encoding)+'%LARGE DATA SET')
        else:
            log( tosend)
            
        try:
            conn.sendall(tosend)
        except socket.error, e:
            if isinstance(e.args, tuple):
                log( "errno is %d" % e[0])
                if e[0] == errno.EPIPE:
                    # remote peer disconnected
                    log( "Detected remote disconnect")
                else:
                    # determine and handle different error
                     pass
            else:
                log( "socket error %s" % e)
                self.sock.close()
    # 0 = skip encoding, 1 = encode list and dict, 2 = reserved for future encodings
    def encode(self, encoding, data):
        if encoding == 0:
            return data
        elif encoding == 1:
            return json.dumps(data, separators=(',',':'))
        else:
            return json.JSONEncoder(data)    
    # decode json to dict or list if reqired
    def decode(self, encoding, data):
        if encoding == 0:
            return data
        elif encoding == 1:
            return json.loads(data)
        else:
            return json.JSONDecoder(data)
    def join(self, encoding, pdata, conn, addr):
        self.sendData(0, 'join', 'player'+str(len(self.players)), conn, addr)
    def move(self, encoding, pdata, conn, addr):
        pass
    def look(self, encoding, pdata, conn, addr):
        level = int(pdata[0])
        exp = int(pdata[1])
        location = int(pdata[2])
        ship = int(pdata[3])
        money = int(pdata[4])
        username = str(pdata[5])
        timesPlayed = int(pdata[6])
        armor = int(pdata[7])
        energy = int(pdata[8])
        turrets = str(pdata[9])
        modules = str(pdata[10])
        plugins = str(pdata[11])
        cargo = str(pdata[12])
        lastPlayed = int(pdata[13])
        if lastPlayed == False:
            lastPlayed = 0;
        uid = int(pdata[14])
        cur1 = self.db.cursor()
        try:
            cur1.execute("DELETE FROM wts_players WHERE uid = '%d' LIMIT 1" % (uid))
        except Exception, e:
            log( 'unable to delete')
            log( e)
        cur2 = self.db.cursor()
        try:
            # don't save records from development adddess
            if(str(addr[0]) == 'TESTING_MACHINE_IP'):
                return
            cur2.execute("INSERT INTO wts_players SET uid = '%d', \
                    address = '%s', \
                    times_played = '%d', \
                    level = '%d', \
                    exp = '%d', \
                    location = '%d', \
                    ship = '%d', \
                    money = '%d', \
                    username = '%s', \
                    armor = '%d', \
                    energy = '%d', \
                    turrets = '%s', \
                    modules = '%s', \
                    plugins = '%s', \
                    cargo = '%s', \
                    last_played = '%d'" % \
                    (uid, str(addr[0]), timesPlayed, level, exp, location, ship, money, username, armor, energy, turrets, modules, plugins, cargo, \
                     lastPlayed))
        except Exception, e:
            log( 'unable to save')
            log(e)
        
    def say(self, encoding, pdata, conn, addr):
        uid = ''.join(random.choice(string.digits) for x in range(8))
        self.sendData(0, 'genUID', int(uid), conn, addr)
    def grab(self):
        pass        

def log(logtxt):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    log_file = open("sock_output.txt", "a", 0)
    log_file.write(str(now)+' '+ logtxt+'\n')
    log_file.close()
    print now, logtxt
     
class CLI(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.rows, self.columns = os.popen('stty size', 'r').read().split()
        self.clr()
        PS1='[\h \@]\$ '
        print '\033[5'
        self.prompt = '> '
        self.doc_header = 'Terminal GS Help'
        threading.Thread(target = self.cmdloop).start()
    def clr(self):
        os.system("clear")
        padCount = int(self.columns)
        titlePad = ' ===Terminal Game Server=== '.center(padCount)
        print '\033[32;1;7m\033[40;25;4m\033[150;100'+titlePad+' \033[0m'
        print '\033[2;1H\033[J' #position cursor and clear below
        print '\033[31;1;237;35;25;7m COMMANDS: \033[22m', ' home  stats  log  help  quit '.center(padCount), '\033[0m'
        print '\033[3;1H' #position cursor
        print ''.ljust(padCount, '-')
        print '\033[0m'
        
        # print '\033[4;1H' #position cursor
        #print '\033[J' #clear excess from header
    def do_home(self, arg):
        self.clr()
    def do_stats(self, arg):
        self.clr()
        print len(multiprocessing.active_children()), ' connections'
    def do_log(self, arg):
        self.clr()
        lastLog = self.tail("sock_output.txt", 16)
        print "\n".join(lastLog)
    def do_q(self, arg):
        self.clr()
        self.do_quit(arg)
    def do_quit(self, arg):
        self.clr()
        shutdown = True
        os.system("clear")
        log('Server Shutdown')
        sys.exit(1)
        for wrkr in multiprocessing.active_children():
            wrkr.join()
    def default(self, arg):
        self.clr()
        print arg+' is not a known command. Type help to learn more.'
    def help(self):
       print '\n'
       print 'Type help [command] to learn mree about the commands.'
    def help_home(self):
        self.clr()
        print 'Command Help: Home'
        print '=================================='
        print 'Clear the screen. This is for OCD people.'
    def help_stats(self):
        self.clr()
        print 'Command Help: Stats'
        print '=================================='
        print 'Show information about the terminal server environment.'
    def help_log(self):
        self.clr()
        print 'Command Help: Log'
        print '=================================='
        print 'log - Show the last few entries in the log file.'
    def styleText(self, style, text):
        if style == 'program title':
            return '\033[32;1;7m\033[40;25;4m\033[150;100'+text+' \033[0m'
    def tail(self, filename, n):
        """Returns last n lines from the filename. No exception handling"""
        size = os.path.getsize(filename)
        with open(filename, "rb") as f:
            # for Windows the mmap parameters are different
            fm = mmap.mmap(f.fileno(), 0, mmap.MAP_SHARED, mmap.PROT_READ)
            try:
                for i in xrange(size - 1, -1, -1):
                    if fm[i] == '\n':
                        n -= 1
                        if n == -1:
                            break
                return fm[i + 1 if i else 0:].splitlines()
            finally:
                fm.close()


    
def main():
    try:
        cli = CLI()
        TerminalNode().run()
    except Exception, e:
        log(str(e))
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
    # shortcuts
    do_q = do_quit
if __name__ == '__main__':
    main()