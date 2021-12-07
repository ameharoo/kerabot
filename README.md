# Kerabot
Python-based production server monitor bot

## Installation
Make this on every servers
1. `git clone https://github.com/ameharoo/kerabot.git`
2. `python3 kerabot/main.py install`
3. Create and modify file "`/etc/kera/kera.config.json`" (for non-linux "`./kera.config.json`") with follow contents:

`
{
  "TOKEN": "<Insert here telegram bot token>",
  "PORT": 8181,
  "HOST": "<0.0.0.0 or another hostname>",
  "SECRET": "<Insert here secret. Secret passphrase must be equal with secrets passphrases on all servers>",
  "SERVERS": [
    "localhost:8181",
    "10.0.0.1:8181",
    "<and another hosts>"
  ],
  "allows": []
}
`

## Usage
For "master" server:
`python3 /usr/bin/kera/bin/main.py master`

For "slave" server:
`python3 /usr/bin/kera/bin/main.py slave`
