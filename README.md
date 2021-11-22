# kerabot
Python-based production server monitor bot

## Installation
Make this on every servers
1. Clone this repo
2. Create and modify file "bot.json" with follow contents:

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
`python3 main.bot master`

For "slave" server:
`python3 main.bot slave`
