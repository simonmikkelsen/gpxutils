#!/usr/bin/python
import os
import os.path
import errno

class FileHelper:
    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:    # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def save_json(self, data, folder, file):
        self.mkdir_p(folder)
        fp = open(os.path.join(folder, file), 'w')
        json.dump(data, fp)
        fp.close()
    def save_file(self, data, file):
        fp = open(file, 'w')
        fp.write(data)
        fp.close()
