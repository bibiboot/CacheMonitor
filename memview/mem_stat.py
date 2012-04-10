import re 
import time 
import memcache 
from memcachedview_stats import MemcachedStats 

def human_time(ti): 
    """ Converts the epoch time to human readable time """ 
    return time.strftime("%d-%m-%Y %H:%M", time.localtime(float(ti))) 
    
class mem():
    #regular expression for keys saved in the cache
    _miss_key_regex = re.compile(ur'(.*)_miss$') 
    _hash_key_regex = re.compile(ur'(.*)_hash$')

    def __init__(self, ip='127.0.0.1', port='11211'):
        #connect to the memcache-python
        self.m = memcache.Client([ip+":"+port])
        #connect to the local memcached file
        self.mem_s = MemcachedStats(ip, port)

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

    def slabs(self):
        """
        stats slabs
        stats items
        """
        slab_data = self.m.get_slabs()[0][1]
        slab_chunks = self.m.get_slab_chunks()[0][1]
        #merge the data from stats-slabs and stats-items
        for k, v in slab_chunks.items():
            if slab_data.has_key(k):
                for sub_k, sub_v in slab_chunks[k].items():
                    slab_data[k][sub_k] = sub_v
        #filter the slabs data
        return self.__filter_slab(slab_data)

    def __filter_slab(self, slab_data):
        ban_list = ['cas_hits', 'cas_badval', 'decr_hits', 'delete_hits', 'reclaimed', 'tailrepairs', 'free_chunks_end']
        attr_list = ['total_pages', 'total_chunks', 'chunks_per_page', 'used_chunks', 'total_chunks', 'free_chunks', 'chunk_size', 'mem_requested']
        evict_list = ['evicted', 'evicted_time', 'evicted_unfetched', 'evicted_nonzero', 'outofmemory']
        data_list = ['number', 'cmd_set', 'get_hits','incr_hits']
        #data_list = ['number', 'cmd_set', 'get_hits', 'age', 'incr_hits']
        label_dict = { 'used_chunks': 'used_ch', 'chunks_per_page': 'ch/page', 'number': 'no.', 'expired_unfetched': 'exp_unftch', 'evicted': 'evic',
                       'evicted_time': 'evic_t', 'touch_hits': 'tch_hits', 'total_chunks': 'tot_ch','incr_hits': 'i_hits', 'free_chunks': 'free_ch',
                       'evicted_unfetched': 'evic_unftc', 'age': 'age', 'evicted_nonzero': 'evic_nzero', 'total_pages': 'tot_pgs', 'get_hits': 'hits',
                       'cmd_set': 'set', 'chunk_size': 'ch_size', 'mem_requested': 'mem_req', 'outofmemory': 'out_mem' }
        attr_dict = {}
        data_dict = {}
        sum_slab_hits = 0
        sum_slab_sets = 0
        
        #merging the data_list and evict_list
        data_list = data_list + evict_list
        #separate the data into two dictionaries
        for k,v in slab_data.items():
            attr_dict[k]=dict((label_dict[sub_k], sub_v) for sub_k, sub_v in v.items() if sub_k in attr_list)
            data_dict[k]=dict((label_dict[sub_k], sub_v) for sub_k, sub_v in v.items() if sub_k in data_list)
            #adding the analysis column for attr
            if v.has_key('mem_requested'):
                attr_dict[k]['%wst_mem'] = str(100-(float(v['mem_requested'])/(float(v['used_chunks'])*float(v['chunk_size'])))*100)[:4]
            attr_dict[k]['%capacity'] = str(float(v['used_chunks'])/float(v['total_chunks'])*100)[:4]
            data_dict[k]['hit/set%'] = str((float(v['get_hits'])/float(v['cmd_set']))*100)[:4]

            if k in [ '1', '2', '3','42']:
                #print "not", k, v['get_hits'], v['cmd_set']
                pass
            else:
                #print k, sum_slab_hits, sum_slab_sets
                sum_slab_hits+=int(v['get_hits'])
                sum_slab_sets+=int(v['cmd_set'])
        return attr_dict, data_dict, str(float(sum_slab_hits)/float(sum_slab_sets))
        #return attr_dict, data_dict, str(float(sum_slab_hits))

    def sizes(self):
        """
        stats sizes
        """
        size = self.m.get_stat_sizes()[0][1]
        return size

    def keys(self):
        """
        stats cachedump slab-id count
        using memcachedstats
        """
        #get data from the memcachedstats
        data_dict = self.mem_s.key_details()
        #key=slab_id, value = tuple( #0=key, #1=size, #2=expiry_time)
        for k,v in data_dict.items():
             data_dict[k] = [ (sub_v[0], sub_v[1].split(" ")[0], sub_v[2].split(" ")[0]) for sub_v in v ]
              
        return self.count_miss_hash_keys(data_dict)

    def count_miss_hash_keys(self, data_dict):
        """
        Count the number of normal, miss and hash keys in a particular slab
        Count the total normal, miss and hash keys
        """
        timeline_dict = {}
        count_dict = {}
        #total key
        key, miss_key, hash_key = 0, 0, 0
        for slab_id, value_list in data_dict.items():
            key_count, miss_key_count, hash_key_count = 0, 0, 0
            for value in value_list:
                #key
                key_value = value[0]
                if self._miss_key_regex.findall(key_value):
                    #miss key found
                    miss_key_count+=1
                elif self._hash_key_regex.findall(key_value):
                    #hash key found
                    hash_key_count+=1
                else:
                    #normal key found
                    key_count+=1
                #human_exp_time = human_time(value[2].split(" ")[0])
                human_exp_time = float(value[2].split(" ")[0])
                if timeline_dict.has_key(human_exp_time):
                    timeline_dict[human_exp_time]+=1
                else:
                    timeline_dict[human_exp_time] = 1
            count_dict[int(slab_id)] = {'key_count': key_count, 
                                   'miss_key_count': miss_key_count, 
                                   'hash_key_count': hash_key_count }
            #adding the total count
            key+=key_count
            miss_key+=miss_key_count
            hash_key+=hash_key_count
        total = key + miss_key + hash_key
        """
        now = time.time()
        timeline_dict = { human_time(timeline): str((float(count_exp)/float(total))*100)[:4] 
                                                                     for timeline, count_exp in timeline_dict.items() 
                                                                                                     if float(timeline) > float(now) } 
        """
        timeline_dict = self.__max_min_timeline(timeline_dict)
        miss_p, hash_p, key_p = 0, 0, 0
        if total!=0:
            miss_p, hash_p, key_p = (float(miss_key)/float(total))*100, (float(hash_key)/float(total))*100, (float(key)/float(total))*100 
        return count_dict,{ 'key': str(key_p)[:4], 'miss_key': str(miss_p)[:4], 'hash_key': str(hash_p)[:4] } , timeline_dict 

    def sortby_slab(self, count_dict):
        return [ (slab_id,count_dict[slab_id]) for slab_id in sorted(count_dict) ]
 
    def __max_min_timeline(self, timeline_dict):
        #sorted_timeline_tup = [ ( human_time(exp), timeline_dict[exp] ) for exp in sorted(timeline_dict.keys()) ]
        sorted_exp = sorted(timeline_dict.keys())
        timeline_dict = {}
        expired_count, fresh_count = 0, 0 
        for exp in sorted_exp:
            if exp < time.time():
                expired_count+=1 
            else:
                fresh_count+=1
        if len(sorted_exp) > 0:
            timeline_dict['first-expiry'] = human_time( sorted_exp[0] )
        if len(sorted_exp) > 1:
            timeline_dict['last-expiry'] = human_time( sorted_exp[-1] )
        if len(sorted_exp) > 2:
            timeline_dict['second_last-expiry'] = human_time( sorted_exp[-2] )
        if len(sorted_exp) > 3:
            timeline_dict['third-last-expiry'] = human_time( sorted_exp[-3] )

        timeline_dict.update( { "expired": expired_count, "fresh": fresh_count } ) 
        return timeline_dict 

import pprint
#m = mem()
#m = mem('10.70.16.99', '11211')
#di,b,c = m.slabs()
#pprint.pprint(c)
