Terminal-Game-Server
====================

Terminal GS is a Python 2.7 game socket server that uses MySQL. It's a multiprocess app that can handle a large amount of concurrent clients. 

This was a prototype and some issues were not resolved befor moving on. For example, transferring data between processes effiently. This can be achieved by using a 
treading pool to share data between processes. In the end, we found that it was easier to have multiplue instances of threaded applications for a game server.
