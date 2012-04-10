import re, telnetlib, sys

class MemcachedStats:

    _client = None
    _key_regex = re.compile(ur'ITEM (.*) \[(.*); (.*)\]')
    _slab_regex = re.compile(ur'STAT items:(.*):number')
    _stat_regex = re.compile(ur"STAT (.*) (.*)\r")

    def __init__(self, host='localhost', port='11211'):
        self._host = host
        self._port = port

    @property
    def client(self):
        if self._client is None:
            self._client = telnetlib.Telnet(self._host, self._port)
        return self._client

    def command(self, cmd):
        ' Write a command to telnet and return the response '
        self.client.write("%s\n" % cmd)
        return self.client.read_until('END')

    def key_details(self, sort=True):
        ' Return a list of tuples containing keys and details '
        cmd = 'stats cachedump %s 10'
        keys = [ (key,slab_id) for slab_id in self.slab_ids()
            for key in self._key_regex.findall(self.command(cmd % slab_id))]
        data_dict = {}
        for key in keys:
            if data_dict.has_key(key[1]):
                data_dict[key[1]].append(tuple(key[0]))
            else:
                a_list = []
                a_list.append(tuple(key[0]))
                data_dict[key[1]] = a_list
        return data_dict

    def keys(self, sort=True):
        ' Return a list of keys in use '
        return [key[0] for key in self.key_details(sort=sort)]

    def slab_ids(self):
        ' Return a list of slab ids in use '
        return self._slab_regex.findall(self.command('stats items'))

    def stats(self):
        ' Return a dict containing memcached stats '
        return dict(self._stat_regex.findall(self.command('stats')))

def main(argv=None):
    if not argv:
        argv = sys.argv
    host = argv[1] if len(argv) >= 2 else '127.0.0.1'
    port = argv[2] if len(argv) >= 3 else '11211'
    import pprint
    m = MemcachedStats(host, port)
    pprint.pprint(m.key_details())

if __name__ == '__main__':
    main()
