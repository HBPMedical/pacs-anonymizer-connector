import argparse
from netdicom.applicationentity import AE
from netdicom.SOPclass import *
from dicom.dataset import Dataset, FileDataset
from dicom.UID import ExplicitVRLittleEndian, ImplicitVRLittleEndian, \
    ExplicitVRBigEndian
import tempfile
import signal
import sys
import pandas as pd
from os import path
from datetime import datetime

# parse commandline
parser = argparse.ArgumentParser(description='storage SCU example')
parser.add_argument('remotehost')
parser.add_argument('remoteport', type=int)
parser.add_argument('-p', '--port', help='local server port', type=int, default=1234)
parser.add_argument('-t','--aet', help='calling AET title', default='ACME1')
parser.add_argument('-m','--aem', help='calling AEM title', default='ACME1')
parser.add_argument('-c','--aec', help='called AEC title', default='COMMON')
parser.add_argument('-i','--implicit', action='store_true',
                    help='negociate implicit transfer syntax only',
                    default=False)
parser.add_argument('-o','--output', help='output folder', default=tempfile.gettempdir())
parser.add_argument('-C','--csv', help='csv file with already processed dicoms', default='dicoms_processed.csv')
parser.add_argument('-e','--explicit', action='store_true',
                    help='negociate explicit transfer syntax only',
                    default=False)

args = parser.parse_args()

# this si called aet in the python library, but we are keeping Thanhs script name
ouput = "../out/"

if args.implicit:
    ts = [ImplicitVRLittleEndian]
elif args.explicit:
    ts = [ExplicitVRLittleEndian]
else:
    ts = [
        ExplicitVRLittleEndian,
        ImplicitVRLittleEndian,
        ExplicitVRBigEndian
    ]

def OnAssociateResponse(association):
    print "Association response received"


def OnAssociateRequest(association):
    print "Association resquested"
    return True

def OnReceiveStore(SOPClass, ds):
    print "Received SOPInstanceUID", ds.SOPInstanceUID
    # do something with dataset. For instance, store it.
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    # !! Need valid UID here
    file_meta.MediaStorageSOPInstanceUID = "1.2.3"
    # !!! Need valid UIDs here
    file_meta.ImplementationClassUID = "1.2.3.4"
    filename = '%s/%s.dcm' % (args.output, ds.SOPInstanceUID)
    fileds = FileDataset(filename, {},
                     file_meta=file_meta, preamble="\0" * 128)
    fileds.update(ds)
    #fileds.is_little_endian = True
    #fileds.is_implicit_VR = True
    fileds.save_as(filename)
    print "File %s written" % filename
    # must return appropriate status
    return SOPClass.Success

# create application entity
MyAE = AE(args.aet, args.port, [PatientRootFindSOPClass,
                             PatientRootMoveSOPClass,
                             VerificationSOPClass], [StorageSOPClass], ts)

MyAE.OnAssociateResponse = OnAssociateResponse
MyAE.OnAssociateRequest = OnAssociateRequest
MyAE.OnReceiveStore = OnReceiveStore
MyAE.start()

# this is to force a quit on ctrl-c (sigint)
# the extra thread created to receive dicoms is not killed automatically
def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    MyAE.Quit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# remote application entity
RemoteAE = dict(Address=args.remotehost, Port=args.remoteport, AET=args.aec)

def list_pacs(dataset):    
    assoc = MyAE.RequestAssociation(RemoteAE)
    st = assoc.PatientRootFindSOPClass.SCU(dataset, 1)
    items = [ss[1] for ss in st if ss[1]]
    assoc.Release(0)
    return items

def copy_dicom(dataset):    
    assoc = MyAE.RequestAssociation(RemoteAE)
    gen = assoc.PatientRootMoveSOPClass.SCU(dataset, args.aem, 1)
    for gg in gen:
        print "gg!", gg
    assoc.Release(0)

# create association with remote AE
print "Requesting association"
assoc = MyAE.RequestAssociation(RemoteAE)
# perform a DICOM ECHO
print "DICOM Echo ... ",
st = assoc.VerificationSOPClass.SCU(1)
print 'done with status "%s"' % st
assoc.Release(0)

d = Dataset()
d.QueryRetrieveLevel = "PATIENT"
d.SOPInstanceUID = '*'

items = list_pacs(d)

# opens the csv file with the already processed items
if path.isfile(args.csv):
    processed = pd.read_csv(args.csv, index_col=0)
else:
    processed = pd.DataFrame(columns=['processed_date'])
    processed.to_csv(args.csv)

# will update the file by append the new lines 
with open(args.csv, 'a') as csv_file:
    for i in items:
        if i.SOPInstanceUID in processed.index:
            print "Already processed ", i.SOPInstanceUID
        else:
            print "found new item, copying"
            print i
            # writes a new line in the csv file so that it remembers the next time
            csv_file.write("%s,%s\n" % (i.SOPInstanceUID, datetime.now()))
            copy_dicom(i)
 
# done
MyAE.Quit()
