#!/usr/bin/python

import re
import curses
import time
from mem_stat import mem
from datetime import timedelta 

"""
Pages
1: Stats
2: Slabs
3: Dump
4: Items sizes

Keys
up or down: Traverse pages.
r         : refresh
q         : Quit
"""

m = mem('127.0.0.1', '11211')

#Geomteric settings
TOTAL_PAGES = 5
SCREEN_WIDTH = 10                             #Default screen width
SCREEN_HEIGHT = 10                            #Default screen height
STATS_X = 0                                   #Starting x cordinate of the stats grid
STATS_Y = 0                                   #Starting y cordinate of the stats grid
SLABS_X = 0                                   #Starting x cordinate of the slabs grid
SLABS_Y = 40                                  #Starting y cordinate of the slabs grid                            
DUMP_X  = 0                                   #Starting x cordinate of the dump grid
DUMP_Y  = 80                                  #Starting y cordinate of the dump grid
SIZES_X = 0                                   #Starting x cordinate of the sizes grid
SIZES_Y = 120                                  #Starting y cordinate of the sizes grid
MAX_MYPAD_HEIGHT = 10                         #Maximum height of mypad
IS_HELP = False

class curses_screen:
    def __enter__(self):
        self.stdscr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(1)
        SCREEN_HEIGHT, SCREEN_WIDTH = self.stdscr.getmaxyx()
        return self.stdscr
    def __exit__(self,a,b,c):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

def comma(amount):
    """
    Converts a string to a comma separated human readable form.
    """
    orig = amount
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>,\g<2>', amount)
    if orig == new:
        return new
    else:
        return comma(new)

def human_time(ti):
    """
    Converts the epoch time to human readable time
    """
    return time.strftime("%d %b %Y %H:%M", time.localtime(float(ti)))

def humanize_time(secs): 
    """
    Convert the seconds to hours and minutes
    """
    d = timedelta(seconds=int(secs)) 
    return str(d)

def convert_bytes(bytes):
    """
    Convert the bytes to human readable Kb, Mb, Gb or Tb format
    """
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fTb' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fGb' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fMb' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fKb' % kilobytes
    else:
        size = '%.2fB' % bytes
    return size

def stats_data(box):
    """
    Page 1
    command - stats
    """
    stats_dict, analysis_dict = m.stats()
    global SLABS_Y
    x, y = STATS_X, STATS_Y
    box.addstr(y, x, "Stats:", curses.A_BOLD)
    y+=2
    for k, v in stats_dict.items():
        #add column heading
        box.addstr(y, x, k, curses.A_BOLD)
        #filter data
        if k in ['time']:
            v = human_time(v)
        elif k in ['limit_maxbytes', 'bytes_written', 'bytes_read', 'bytes']:
            v = convert_bytes(v)
        elif k in ['uptime']:
            v = humanize_time(str(v))
        elif k not in ['version', 'rusuage_system', 'rusuage_user']:
            v = comma(v)
        box.addstr(y+1, x, v)
        x+=25
        #break the line if the columns exceed the screen width
        if x == (STATS_X + 25*6):
            x, y = STATS_X, y+3
    #draw the analysis graph 
    draw_analysis_grid(box, analysis_dict, y, x, "Stats")
    
    #Extending the page if data is large
    if y > SLABS_Y:
        SLABS_Y = y + 2

def slabs_data(box):
    """
    Page:2
    command - stats slabs and stats items
    """
    global SIZES_Y
    attr_dict, data_dict, hit_set = m.slabs()
    #add heading 
    box.addstr(SLABS_Y, SLABS_X, "Slabs:", curses.A_BOLD)
    attr_y = SLABS_Y + 2
    data_y = attr_y + len(attr_dict) + 2
    evict_y = data_y + len(data_dict) + 2
    draw_slab_grid(box, attr_dict, attr_y)
    end_y = draw_slab_grid(box, data_dict, data_y)
    box.addstr(end_y+4, 0, "Hit/Set slab except 1,2,3, 36 and 41 : ")
    box.addstr(end_y+4, 40, hit_set)
    if end_y > SIZES_Y:
        SIZES_Y = end_y + 2

def dump_data(box):
    """
    Page 3
    stats cachedump slab
    """
    x, y = DUMP_X, DUMP_Y
    box.addstr(y, x, "Dump:", curses.A_BOLD)
    y+=2
    box.addstr(y, x, "Slab", curses.A_BOLD)
    y+=1
    keys_count_dict, analysis_dict, timeline_dict = m.keys()
    slab_key_list = m.sortby_slab(keys_count_dict)
    label = True
    for slab_tup in slab_key_list:
        slab_id = slab_tup[0]
        count_dict = slab_tup[1]
        box.addstr(y, x, str(slab_id))
        x+=5
        """
        for k,v in count_dict.items():
            if label:
                box.addstr(y-1, x, "keys")
                box.addstr(y-1, x+5, "miss")
                box.addstr(y-1, x+10, "hash")
                label = False 
            box.addstr(y, x, str(v))
            x+=5
        """
        if label:
            box.addstr(y-1, x, "keys")
            box.addstr(y-1, x+5, "miss")
            box.addstr(y-1, x+10, "hash")
            label = False
        box.addstr(y, x, str(count_dict['key_count']))
        box.addstr(y, x+5, str(count_dict['miss_key_count']))
        box.addstr(y, x+10, str(count_dict['hash_key_count']))
         
        x = DUMP_X
        y+=1
    
    y+=3
    #analysis heading
    box.addstr(y, STATS_X, "Dump - Analysis", curses.A_BOLD)
    #draw the heading lines
    for i in range(0, SCREEN_WIDTH):
        box.addch(y+1, i, curses.ACS_BSBS)
        box.addch(y+12, i, curses.ACS_BSBS)
        box.addch(y+14, i, curses.ACS_BSBS)

    #draw the graph
    x, y = 0, y+12
    for k, v in analysis_dict.items():
        #column name
        box.addstr(y+1, x+1, k, curses.A_BOLD)
        #draw the graph lines
        for i in range(1,int(int(float(v))/10)+1):
            box.addch(y-i, x+2, curses.ACS_BSBS)
        #write the value
        box.addstr(y, x+1, str(v)+"%")
        #jump to the next column
        x+=10
    #draw_analysis_grid(box, analysis_dict,y, x, "Analysis")
    draw_analysis_grid2(box, timeline_dict, y, x, "Timeline")
    

def sizes_data(box):
    """
    Page 4
    command - stats sizes
    """
    size_dict = m.sizes()
    sorted_keys = [str(key) for key in sorted(int(k) for k in size_dict.keys()) ]
    x, y = SIZES_X, SIZES_Y
    #add a label to table
    box.addstr(y, x, "Item - Sizes:", curses.A_BOLD)
    y+=2
    for k in sorted_keys:
        v = size_dict[k]
        box.addstr(y, x, "%10s"%str(convert_bytes(k)), curses.A_BOLD)
        box.addstr(y, x+12, "%7s"%str(comma(v)))
        y+=1
        if y > SIZES_Y + len(sorted_keys)/3 + 1:
            x, y = x+ 20, SIZES_Y+2

def help():
    help_pad = curses.newpad(MAX_MYPAD_HEIGHT, SCREEN_WIDTH)        
    help_pad.addstr(0, 0, "Help page:", curses.A_BOLD)
    y = 2
    f = open('doc', 'r')
    for line in f:
        help_pad.addstr(y, 0, line)
        y+=1
    help_pad.refresh(0, 0, 0, 0,SCREEN_HEIGHT, SCREEN_WIDTH)

def draw_analysis_grid(box, anal_dict, y, x, title):
    y+=5
    #analysis heading
    box.addstr(y, STATS_X, title+" - Analysis", curses.A_BOLD)
    #draw the heading lines
    for i in range(0, SCREEN_WIDTH):
        box.addch(y+1, i, curses.ACS_BSBS)
        box.addch(y+12, i, curses.ACS_BSBS)
        box.addch(y+14, i, curses.ACS_BSBS)

    #draw the graph
    x, y = 0, y+12
    for k, v in anal_dict.items():
        #column name
        box.addstr(y+1, x+1, k, curses.A_BOLD)
        #draw the graph lines
        for i in range(1,int(int(float(v))/10)+1):
            box.addch(y-i, x+2, curses.ACS_BSBS)
        #write the value
        box.addstr(y, x+1, str(v)+"%")
        #jump to the next column
        x+=10
        if x > SCREEN_WIDTH:
            x = 0
            y = y+10

def draw_analysis_grid2(box, anal_dict, y, x, title):
    y+=5
    #analysis heading
    box.addstr(y, STATS_X, title+" - Analysis", curses.A_BOLD)
    #draw the heading lines
    for i in range(0, SCREEN_WIDTH):
        box.addch(y+1, i, curses.ACS_BSBS)
        #box.addch(y+12, i, curses.ACS_BSBS)
        #box.addch(y+14, i, curses.ACS_BSBS)

    #draw the graph
    x, y = 0, y+2
    for k, v in anal_dict.items():
        #column name
        box.addstr(y, x+1, k, curses.A_BOLD)
        #write the value
        box.addstr(y, x+20, str(v))
        #jump to the next column
        y+=1
        if x > SCREEN_WIDTH:
            x = 0
            y = y+3


def draw_slab_grid(box, slab_dict, y):
    allow_label = True
    x = SLABS_X
    sorted_list = sorted( int(slab_id) for slab_id in slab_dict.keys())
    for slab_id in sorted_list:
        if allow_label:
            box.addstr(y, x, "slab", curses.A_BOLD)
        box.addstr(y+1, x, str(slab_id)) 
        x+=7
        for sub_k, sub_v in slab_dict[str(slab_id)].items():
            if sub_k in ['mem_req', 'ch_size']:
                sub_v = convert_bytes(sub_v)
            elif sub_k in ['age']:
                sub_v = humanize_time(sub_v)
            elif sub_v in ['%usd_mem']:
                pass
            else:
                sub_v = comma(sub_v)
            if allow_label:
                box.addstr(y, x, sub_k, curses.A_BOLD)
            box.addstr(y+1, x, sub_v)
            x+=13
        x, y = SLABS_X, y+1
        allow_label = False
    return y


def draw_page(mypad_pos):
    if mypad_pos == 0:
        #Page-1
        stats_data(mypad)
    elif mypad_pos == SCREEN_HEIGHT:
        pass
        #Page-2
        #slabs_data(mypad)
    elif mypad_pos == SCREEN_HEIGHT*2:
        pass
        #Page-3
        #dump_data(mypad)
    else:
        pass
        #Page-4
        #sizes_data(mypad)

def screen(stdscr):
    """
    Create screens and pads
    Setup the height, width attribute
    """
    global SCREEN_HEIGHT, SCREEN_WIDTH, MAX_MYPAD_HEIGHT, SLABS_Y, DUMP_Y, SIZES_Y
    SCREEN_HEIGHT, SCREEN_WIDTH = stdscr.getmaxyx()
    SCREEN_HEIGHT, SCREEN_WIDTH = SCREEN_HEIGHT - 1, SCREEN_WIDTH - 1
    MAX_MYPAD_HEIGHT = SCREEN_HEIGHT*TOTAL_PAGES
    SLABS_Y = (MAX_MYPAD_HEIGHT/TOTAL_PAGES)+1
    DUMP_Y = SLABS_Y*2 +5 
    SIZES_Y = SLABS_Y*4
    mypad = curses.newpad(MAX_MYPAD_HEIGHT, SCREEN_WIDTH)
    return mypad

#m = mem('10.70.16.99', '11211')

with curses_screen() as stdscr:
    """
    Execution of the curses begins here.
    """
    #Create the screen
    mypad = screen(stdscr)

    #Load data from mem
    stats_data(mypad)
    mypad_pos = 0
    #mypad.addstr(0, 20, str(SIZES_Y))
    mypad.refresh(mypad_pos, 0, 0, 0, SCREEN_HEIGHT, SCREEN_WIDTH)
    while True:
        #Wait for the user input
        cmd = mypad.getch()

        #mypad.addstr(0, 0, str(cmd))
        if cmd == 66:
            #Pressed Keydown
            IS_HELP = False
            mypad_pos+= SCREEN_HEIGHT
            if mypad_pos >= MAX_MYPAD_HEIGHT:
                mypad_pos-=SCREEN_HEIGHT
            draw_page(mypad_pos)
        elif cmd == 65:
            #Pressed Keyup
            IS_HELP = False
            mypad_pos-= SCREEN_HEIGHT
            if mypad_pos < 0:
                mypad_pos = 0
            draw_page(mypad_pos)
        elif cmd == ord('q'):
            #Pressed 'q'
            if IS_HELP:
                mypad.refresh(mypad_pos, 0, 0, 0, SCREEN_HEIGHT, SCREEN_WIDTH)
                IS_HELP = False
            else:
                break
        elif cmd == ord('r'):
            #Pressed r for refresh
            IS_HELP = False
            draw_page(mypad_pos)
        elif cmd == ord('h'):
            IS_HELP = True
            help()    
        #For the rest of the keys
        if IS_HELP is False:
            mypad.refresh(mypad_pos, 0, 0, 0, SCREEN_HEIGHT, SCREEN_WIDTH)
        else:
            help_pad.refresh(mypad_pos, 0, 0, 0, SCREEN_HEIGHT, SCREEN_WIDTH)
