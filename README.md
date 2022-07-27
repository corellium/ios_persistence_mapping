# Mapping iOS Persistence Attack Surface using Corellium

Accompanying code for a blog post (**TODO: Link to the post**).

This repository contains a `uniq_opens.txt` file as generated in the blog post. Replace this file if new data is generated.

## Setup

1. Install Neo4J Desktop or create [AuraDB](https://neo4j.com/cloud/platform/aura-graph-database/) instance
2. Run `brew install libmagic`
3. Run `python3 -m pip install -r requirements.txt` in the project root
4. Run `npm install` in the project root
5. Download and unpack the target IPSW and mount the root filesystem
6. Run `diskutil enableOwnership /Volumes//Volumes/SkyF19F77.D10D101D20D201OS` (or whatever the actual mount point is)
7. Edit the `process_opens.py` script so that `ROOT_FS_PATH` is the mount point of the filesystem
8. Edit the `process_opens.py` script to fill in the Neo4J credentials/host
9. Copy `config.json.example` to `config.json` and fill in the Corellium credentials, project name, and device UUID
10. Invoke the script: `sudo python3 process_opens.py` (as root because we enable permissions on the FS)

Once complete, validate that the data imported successfully by running this Cypher query in the Neo4J Browser:

```
MATCH (p:Process) RETURN p
```
