Terminal Game Server
====================

Terminal GS is a Python 2.7 game socket server that uses MySQL. It's a multiprocess app that can handle many concurrent users. 

This was a prototype and some issues were not resolved before moving on. For example, efficiently transferring data between processes was never solved in the code. It should be possible to fix by using a treading pool to pipe data between processes. In the end, we found that it was easier to have multiple instances of threaded applications for a game server.
