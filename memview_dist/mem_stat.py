import re 
import time 
import memcache 
from util import *

class mem():

    def __init__(self, ip='127.0.0.1', port='11211'):
        #connect to the memcache-python
        self.host = "%s:%s" % ( ip,port )
        self.m = memcache.Client([ip+":"+port])

    def stats(self):
        """
        stats
        """
        #data from the cache
        stats_dict = self.m.get_stats()[0][1]
        #filter for analysis
        stats_analysis = self.__stats_analysis(stats_dict)
        return stats_dict, stats_analysis

    def __stats_analysis(self, stats_dict):
        """
        hits%, miss%, get%, set%, occupy%, unfteched_evicted%, unfetched_expired%
        """
        hits_p, miss_p, get_p, set_p, unftch_evict, unftch_exp = 0, 0, 0, 0, 0, 0
        ana_dict = {}
        if float(stats_dict['cmd_get'])!=0:
            #percentage hits, miss
            hits_p = float(stats_dict['get_hits'])/float(stats_dict['cmd_get'])*100
            miss_p = float(stats_dict['get_misses'])/float(stats_dict['cmd_get'])*100
        if float(stats_dict['cmd_get'])!=0 or float(stats_dict['cmd_set'])!=0:
            #percentage gets, sets
            get_p = (float(stats_dict['cmd_get'])/(float(stats_dict['cmd_get'])+float(stats_dict['cmd_set'])))*100
            set_p = 100 - get_p
        #percentage occupied
        occupy_p = (float(stats_dict['bytes'])/float(stats_dict['limit_maxbytes']))*100
        if stats_dict.has_key('evicted_unfetched'):
            if float(stats_dict['evictions'])!=0:
                #percentage evicted unfetched out of total evicted
                unftch_evict = float(stats_dict['evicted_unfetched'])/float(stats_dict['evictions'])*100
            ana_dict['unftc_ev'] = "%.2f"%unftch_evict
        if stats_dict.has_key('expired_unfetched'):
            if float(stats_dict['total_items'])!=0:
                #percentage expired unfetched out of total items
                unftc_exp = (float(stats_dict['expired_unfetched'])/float(stats_dict['total_items']))*100
            ana_dict['expired_unfetched'] = "%.2f"%unftc_exp
        ana_dict.update({ "hits": "%.2f"%hits_p, 'miss': "%.2f"%miss_p, "get": "%.2f"%get_p, "set": "%.2f"%set_p, "occupy": "%.2f"%occupy_p})
        return ana_dict 
