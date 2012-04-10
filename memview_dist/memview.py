#!/usr/bin/python

import curses
from util import *
from mem_stat import mem

"""
Pages
1: Stats memcache1
2: Stats memcache2
3: Stats memcache3

Keys
up or down: Traverse pages.
r         : refresh
q         : Quit
"""

#Geomteric settings
TOTAL_PAGES = 3
SCREEN_WIDTH = 10                             #Default screen width
SCREEN_HEIGHT = 10                            #Default screen height
PAGE1_X = 0                                   #Starting x cordinate of the stats grid
PAGE1_Y = 0                                   #Starting y cordinate of the stats grid
PAGE2_X = 0                                   #Starting x cordinate of the slabs grid
PAGE2_Y = 40                                  #Starting y cordinate of the slabs grid                            
PAGE3_X  = 0                                   #Starting x cordinate of the dump grid
PAGE3_Y  = 80                                  #Starting y cordinate of the dump grid
MAX_MYPAD_HEIGHT = 10                         #Maximum height of mypad

m1 = mem('127.0.0.1', '11211')
m2 = mem('127.0.0.1', '11212')
m3 = mem('127.0.0.1', '11213')

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

def stats_data(box, m,x=0, y=0):
    """
    Page 1
    command - stats
    """
    stats_dict, analysis_dict = m.stats()
    box.addstr(y, x, "Stats: "+str(m.host), curses.A_BOLD)
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
        if x == (PAGE1_X + 25*6):
            x, y = PAGE1_X, y+3
    #draw the analysis graph 
    draw_analysis_grid(box, analysis_dict, y, x, "Stats")
    

def draw_analysis_grid(box, anal_dict, y, x, title):
    y+=5
    #analysis heading
    box.addstr(y, PAGE1_X, title+" - Analysis", curses.A_BOLD)
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

def draw_page(mypad_pos):
    """
    Draw page according to the mypad_pos
    """
    if mypad_pos == 0:
        #Page-1
        stats_data(mypad, m1, PAGE1_X, PAGE2_Y)
    elif mypad_pos == SCREEN_HEIGHT:
        #Page-2
        stats_data(mypad, m2 ,PAGE2_X, PAGE2_Y)
    else:
        #elif mypad_pos == SCREEN_HEIGHT*2:
        #Page-3
        stats_data(mypad, m3, PAGE3_X, PAGE3_Y)

def screen(stdscr):
    """
    Create screens and pads
    Setup the height, width attribute
    """
    global SCREEN_HEIGHT, SCREEN_WIDTH, MAX_MYPAD_HEIGHT, PAGE2_Y, PAGE3_Y
    SCREEN_HEIGHT, SCREEN_WIDTH = stdscr.getmaxyx()
    SCREEN_HEIGHT, SCREEN_WIDTH = SCREEN_HEIGHT - 1, SCREEN_WIDTH - 1
    MAX_MYPAD_HEIGHT = SCREEN_HEIGHT*TOTAL_PAGES
    PAGE2_Y = (MAX_MYPAD_HEIGHT/TOTAL_PAGES)
    PAGE3_Y = PAGE2_Y*2 + 1
    mypad = curses.newpad(MAX_MYPAD_HEIGHT, SCREEN_WIDTH)
    return mypad

with curses_screen() as stdscr:
    """
    Execution of the curses begins here.
    """
    #Create the screen
    mypad = screen(stdscr)

    #Load data from mem
    stats_data(mypad, m1)
    mypad_pos = 0
    mypad.refresh(mypad_pos, 0, 0, 0, SCREEN_HEIGHT, SCREEN_WIDTH)
    while True:
        #Wait for the user input
        cmd = mypad.getch()
        if cmd == 66:
            #Pressed Keydown
            mypad_pos+= SCREEN_HEIGHT
            if mypad_pos >= MAX_MYPAD_HEIGHT:
                mypad_pos-=SCREEN_HEIGHT
            draw_page(mypad_pos)
        elif cmd == 65:
            #Pressed Keyup
            mypad_pos-= SCREEN_HEIGHT
            if mypad_pos < 0:
                mypad_pos = 0
            draw_page(mypad_pos)
        elif cmd == ord('q'):
            #Pressed 'q'
                mypad.refresh(mypad_pos, 0, 0, 0, SCREEN_HEIGHT, SCREEN_WIDTH)
                break
        elif cmd == ord('r'):
            #Pressed r for refresh
            draw_page(mypad_pos)
        mypad.refresh(mypad_pos, 0, 0, 0, SCREEN_HEIGHT, SCREEN_WIDTH)
