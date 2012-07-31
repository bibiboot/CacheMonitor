Overview
========================

**Author:** dan-boa

cachemonitor is a lightweight memcache monitoring tool written on python curses. It jells up with your terminal and loads lazily the statistics from the memcache server.

Usage
========================

memview folder is for single memcache monitoring in a more detailed fashion.
memview_dist is for distributed memcache monitoring on a basic level.

    For single memcache monitoring.
    cd memview
    python memview.py

    For distributed memcache monitoring.
    cd memview_dist
    python memview.py

Setting changes
========================

Make the following changes corresponding to the server address of the memcache being monitored.

    vim memview/memview.py
    # Solo memcache
    m = mem('127.0.0.1', '11211')

    vim memview_dist/memview.py
    # Memcache 1
    m1 = mem('127.0.0.1', '11211')
    # Memcache 2
    m2 = mem('127.0.0.1', '11212')
    # memcache 3
    m3 = mem('127.0.0.1', '11213')


Commands
========================

    **Keys**
    up or down: Traverse pages.
    r         : Refresh.
    q         : Quit.

