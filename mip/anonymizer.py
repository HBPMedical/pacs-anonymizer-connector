from subprocess import call, Popen
import subprocess
import os

class DicomAnonymizer:
    def __init__(self, jar, quarantine, config,  lookupTable=None):        
        self.path = os.path.abspath(jar)        
        self.lookupTable = lookupTable
        self.quarantine = os.path.abspath(quarantine)
        self.config = os.path.abspath(config)
    def anonymize(self, target):
        #TODO: see if the hardcoded values like the class to load from the jar are ok
        #java -Dlogback.configurationFile=./logback.xml -cp lib/pandora-clients-fedehr-anonymiser-cli-1.0.0.jar fr.maatg.fedehr.anonymiser.cli.DicomAnonymizerCli
        cmd = ["java  -Dlogback.configurationFile=./logback.xml" +
                " -cp " + self.path,
                " fr.maatg.fedehr.anonymiser.cli.DicomAnonymizerCli", 
                " -q " + self.quarantine,
                " -s " + self.config,
                " -target " + target
            ]
         

        if self.lookupTable:
            args.append( "-lookupTable " + os.path.abspath(self.lookupTable))
        print "about to execute: ", cmd
#        status = call(cmd , shell=True)
        p = Popen(
            cmd, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE,
        )

        for n in range(8):
            print p.stdout.readline()
        print >>p.stdin, "r\n"
        print proc.stdout.readline()
        print >>p.stdin, "y\n"
        print proc.stdout.readline()
        print proc.stdout.readline()
        print >>p.stdin, "t\n"
        status = proc.comunicate("\n")
        return status
