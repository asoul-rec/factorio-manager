# Factorio Manager

## Run

```shell
python -m facmgr.client [OPTIONS]  # run the client
python -m facmgr.server [OPTIONS]  # run the server
```

## Project structure

Factorio Manager can be separate into 2 parts

1. Factorio server + Manager server 
2. Manager client + Telegram bot server

Factorio server and Telegram bot server provide gaming and controlling functions to the end-users.
Part 1. and 2. can be deployed on different machines or on the same machine.

## Features
(items with * is WIP)
1. [ ] server manager (daemon)
   1. [x] server options
      1. [x] start/stop/restart the server process, load with specified savefile, custom starting args
      2. [x] log manager, in-game command
   2. [x] savefile explorer (at least get name & play time from the saves, can be JSON/do not need to be human friendly)
   3. [ ] communication: 
      1. [x] grpc server
      2. [ ] authentication, ensure consistency
2. [x] middle layer: tg bot / server manager client
   1. [x] connect to server manager
   2. ~~connect to factorio with rcon~~ (use custom grpc functions to support in-game command)
3. [ ] tg bot frontend
   1. [x] easy interface to set configurations
   2. [x] basic function: switch saves. show save metadata to choose the correct one
   3. [x] realtime chat and status with long polling / message forwarding
   4. [x] run in-game commands (just transfer the raw command).
   5. [ ] process the response of the in-game commands (as string in lua? how to deal with it when an error occurs?)
