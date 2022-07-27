#!/usr/bin/env python3
import json
import os

import magic
import delegator
from py2neo import Graph


ROOT_FS_PATH = '/Volumes/SkyF19F77.D10D101D20D201OS'
LOGFILE = 'uniq_opens.txt'

NEO4J_USERNAME = 'neo4j'
NEO4J_PASSWORD = 'hunter2'

# For AuraDB:
NEO4J_HOST = 'neo4j+s://randomly-generated.databases.neo4j.io'

# For local Neo4J Desktop:
# NEO4J_HOST = "bolt://127.0.0.1:7687"



class Process():
    def __init__(self, name):
        self.name = name

        if len(name) >= 15:
            # Could be a partial name
            search_name = name + '*'
        else:
            search_name = name

        cmd = 'find "{}" -name "{}" -type f 2>/dev/null'.format(ROOT_FS_PATH, search_name)
        r = delegator.run(cmd)
        try:
            full_path = r.out.splitlines()[0]
        except IndexError:
            print('Error finding local file "{}": "{}"'.format(search_name, r.out))
            raise

        self.path = '/' + os.path.relpath(full_path, ROOT_FS_PATH)
        self.name = os.path.basename(full_path)

    def create(self):
        return "CREATE (:Process {{name:'{}', path:'{}'}})".format(self.name, self.path)


class Filename():
    def __init__(self, opened_path):
        self.opened_path = opened_path
        self.is_device_file = False
        self.is_missing = False
        self.is_dir = False
        self.file_type = None
        self.owner = None
        self.group = None
        self.perms = 0
        self.size = 0

        # Find the file on the filesystem
        if opened_path.startswith('/dev/'):
            self.is_device_file = True
            return

        # First try local, then remote
        try:
            self._get_local_stat(opened_path)
        except FileNotFoundError:
            print('Unable to find "{}" locally, trying remote...'.format(opened_path))
            self._get_remote_stat(opened_path)
          
    def _get_local_stat(self, opened_path):
        if opened_path.startswith('/'):
            opened_path = opened_path[1:]

        final_path = os.path.join(ROOT_FS_PATH, opened_path)
        if not os.path.exists(final_path):
            raise FileNotFoundError()

        s = os.stat(final_path)
        self.owner = s.st_uid
        self.group = s.st_gid
        self.perms = s.st_mode
        self.size = s.st_size

        if os.path.isdir(final_path):
            self.is_dir = True
            return
        
        self.file_type = magic.from_file(final_path)

    def _get_remote_stat(self, opened_path):
        # Stat the file on the remote device
        cmd = 'node stat_file.js "{}"'.format(opened_path)
        r = delegator.run(cmd)

        if 'NotFound' in r.out:
            print('Unable to find "{}" remotely!'.format(opened_path))
            self.is_missing = True
            return

        try:
            s = json.loads(r.out)
        except json.decoder.JSONDecodeError:
            print(opened_path)
            print(r.out)
            print(r.err)
            raise

        self.owner = s['uid']
        self.group = s['gid']
        self.perms = s['mode']
        self.size = s['size']

        if 'entries' in s.keys():
            # This is a directory
            self.is_dir = True
            return

        # Download the file and check its type
        cmd = 'node download_file.js "{}" ./tmp'.format(opened_path)
        print("Downloading {}...".format(opened_path))
        r = delegator.run(cmd)
        print("Done downloading")
        self.file_type = magic.from_file('./tmp')
        os.unlink('./tmp')

    def create(self):
        attributes = ''
        if self.is_device_file:
            attributes += ':DEVICE_FILE'
        if self.is_missing:
            attributes += ':MISSING'
        if self.is_dir:
            attributes += ':DIRECTORY'
        return "CREATE (:File{} {{path:'{}', type:'{}', owner:'{}', group:'{}', permissions:'{}', size:'{}'}})".format(attributes, self.opened_path, self.file_type, self.owner, self.group, oct(self.perms), self.size)


processes = {}
files = {}

graph = Graph(NEO4J_HOST, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

with open(LOGFILE, 'r') as f:
    for line in f.read().splitlines():
        tx = graph.begin()

        count = line.split()[0]

        try:
            process = line.split('Process: "')[1].split('", Path:')[0]
        except IndexError:
            print("Invalid line:\n\t{}\n".format(line))
            continue

        opened_path = os.path.normpath(line.split('Path: "')[1].split('"')[0])

        print('Process: "{}", Path: "{}"'.format(process, opened_path))

        if process not in processes.keys():
            p = Process(process)
            processes[process] = p
            # print(p.create())
            tx.run(p.create())
        else:
            p = processes[process]

        if opened_path not in files.keys():
            the_f = Filename(opened_path)
            files[opened_path] = the_f
            # print(the_f.create())
            tx.run(the_f.create())
        else:
            the_f = files[opened_path]

        tx.run("MATCH (p:Process {{name: '{}'}}), (f:File {{path: '{}'}}) CREATE (p)-[:OPENED {{count:{}}}]->(f)".format(p.name, the_f.opened_path, count))
        graph.commit(tx)
