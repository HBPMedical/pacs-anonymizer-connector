import argparse
from os import path
from datetime import datetime
import logging
from logging.config import fileConfig
import tempfile
from dicom.dataset import Dataset
from pydicom.datadict import tag_for_name, dictionaryVR

from mip import Pacs, DicomAnonymizer

# parse commandline
parser = argparse.ArgumentParser(description='Download and anonymize files from a PACS system')
#--------------- PACS options ------------------
parser.add_argument('remotehost')
parser.add_argument('remoteport', type=int)
parser.add_argument('-p', '--port', help='local server port', type=int, default=1234)
parser.add_argument('-t','--aet', help='calling AET title', default='HBP')
parser.add_argument('-c','--aec', help='calling AEC call, the data-store', default='COMMON')
parser.add_argument('keys', metavar='KEY', type=str, nargs='+', help='search keys')
parser.add_argument('-l','--log', help='configuration log file', default='logging.ini')
parser.add_argument('-r','--queryRetrieveLevel', help='query retrieve level', default='PATIENT')
args = parser.parse_args()

if path.isfile(args.log):
    fileConfig(args.log)
else:
    logging.warning("could not find configuration log file '%s'" % args.log)

#starts our pacs instance
pacs = Pacs( args.port,
            args.aet)

pacs.connect(args.remotehost, 
            args.remoteport, 
            args.aec)

ds = Dataset()
ds.QueryRetrieveLevel = args.queryRetrieveLevel
for k in args.keys:
    parts=k.split('=')
    tag = tag_for_name(parts[0])
    ds.add_new(tag, dictionaryVR(tag) , parts[1])

items = pacs.query(ds)

for i in items:
    print '---'
    print i


