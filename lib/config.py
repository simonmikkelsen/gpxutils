import os
import os.path
 
class MapillaryConfig:
    def __init__(self):
        self.configDir = os.path.join(os.path.expanduser('~'), '.mapillary')
        self.config_file = os.path.join(self.configDir, "config.txt")
        self.values = {}
    
        self.read()
    def read(self):
        self.values = {}
        if not os.path.isfile(self.config_file):
            return
        
        config = None
        with open(self.config_file, 'r') as f:
            config = f.readlines()
        if config == None:
            raise "Failed to read config from '%s'." % self.config_file
            
        for line in config:
            line = line.strip()
            if len(line) == 0 or line.find("#") == 0:
                continue
            index = line.find("=")
            if index == -1:
                print "Line in '%s' does not contain a =:%s" % (self.config_file, line)
            key = line[:index]
            value = line[index:+1]
            self.values[key] = value
    def save(self):
        if not os.path.exists(self.configDir):
            os.makedirs(self.configDir)
    
        output = []
        for key in self.values.keys():
            output.append("=".join([key, self.values[key]]))
        
        with open(self.config_file, 'w') as file:
           file.write("\n".join(output))
    def getClientID(self):
        return self._get('client_id')
    def setClientID(self, client_id):
        self._set('client_id', client_id)
    def _get(self, key):
        if not key in self.values:
            return None
        return self.values[key]
    def _set(self, key, value):
        self.values[key] = value
