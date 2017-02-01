from subprocess import call
import os

class DicomAnonymizer:
    def __init__(self, jar, quarantine, config,  lookupTable=None):        
        self.path = os.path.abspath(jar)        
        self.lookupTable = lookupTable
        self.quarantine = os.path.abspath(quarantine)
        self.config = os.path.abspath(config)
    def anonymize(self, target):
        #TODO: see if the hardcoded values like the class to load from the jar is ok
        #java -Dlogback.configurationFile=./logback.xml -cp lib/pandora-clients-fedehr-anonymiser-cli-1.0.0.jar fr.maatg.fedehr.anonymiser.cli.DicomAnonymizerCli
        cmd = ['java', 
                '-Dlogback.configurationFile=./logback.xml',
                '-cp', self.path,
                'fr.maatg.fedehr.anonymiser.cli.DicomAnonymizerCli',
                '-q', self.quarantine, 
                '-s', self.config,
                '-target', target]
        if self.lookupTable:
            cmd.extend(['-lookupTable', os.path.abspath(self.lookupTable)])
        print "about to execute"
        status = call(" ".join(cmd), shell=True)
        return status
