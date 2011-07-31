#!/usr/bin/env python
import tarfile
import cPickle
import os, shutil
import globals

FILE_EXT = '.tar.bz2'
WRITE_MODE = 'w:bz2'
READ_MODE = 'r:bz2'

class SaveFile(object):
    """Saves and loads game data."""
    def __init__(self, filename):
        assert(filename is not None)
        self._filename=filename
    
    def load(self):
        savedir = globals.savefile_location+self._filename
        savefile = savedir+FILE_EXT
        result = {}
        assert(not os.access(savedir, os.F_OK))
        if not os.access(savefile, os.F_OK):
            return None
        tar = tarfile.open(savefile, READ_MODE)
        tar.extractall(globals.savefile_location)
        pickles = os.listdir(savedir)
        print pickles
        assert(len(pickles)>0)
        for pickle in pickles:
            assert(pickle[-7:]=='.pickle')
            with open(savedir+'/'+pickle, 'r') as f:
                result[pickle[:-7]]=cPickle.load(f)
        shutil.rmtree(savedir)
        #os.remove(savefile) #though a common thing to do in roguelikes, this is generally a bad practice; encourages save-scumming by forcing people to make crash backups
        return result

    def save(self, candidates):
        savedir = globals.savefile_location+self._filename
        savefile = savedir+FILE_EXT+'.tmp'
        assert(not os.access(savedir, os.F_OK))
        os.mkdir(savedir)
        tar = tarfile.open(savefile, WRITE_MODE)
        for key,value in candidates.items():
            filename=savedir+'/'+key+'.pickle'
            print key
            with open(filename, 'w') as f:
                cPickle.dump(value, f)
            tar.add(filename)
            os.remove(filename)
        shutil.rmtree(savedir)
        tar.close()
        shutil.move(savefile,savedir+FILE_EXT)
        return

if __name__ == '__main__':
    import unittest

    class SaveFileTest(unittest.TestCase):
        """Test SaveFile functionality."""

        def setUp(self):
            globals.savefile_location='./'

        def test01_save_and_load(self):
            """Testing saving and loading"""
            data_in={'one':1, 'two':2, 'tuple':(True,False,None)}
            savefile=SaveFile('testsave')
            savefile.save(data_in)
            data_out=savefile.load()
            self.assertEqual(data_in, data_out)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(SaveFileTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
