import argparse
from netdicom.applicationentity import AE
from netdicom.SOPclass import *
from dicom.dataset import Dataset, FileDataset
from dicom.UID import ExplicitVRLittleEndian, ImplicitVRLittleEndian, \
    ExplicitVRBigEndian
import netdicom
# netdicom.debug(True)
import tempfile
#import signal
#import sys

# parse commandline
parser = argparse.ArgumentParser(description='storage SCU example')
parser.add_argument('remotehost')
parser.add_argument('remoteport', type=int)
parser.add_argument('searchstring')
parser.add_argument('-p', '--port', help='local server port', type=int, default=1234)
parser.add_argument('-t','--aet', help='calling AET title', default='ACME1')
parser.add_argument('-m','--aem', help='calling AEM title', default='ACME1')
parser.add_argument('-c','--aec', help='called AEC title', default='COMMON')
parser.add_argument('-i','--implicit', action='store_true',
                    help='negociate implicit transfer syntax only',
                    default=False)
parser.add_argument('-o','--output', help='output folder', default=tempfile.gettempdir())
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

def OnReceiveStore(SOPClass, DS):
    print "Received C-STORE", DS.PatientName
    # do something with dataset. For instance, store it.
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    # !! Need valid UID here
    file_meta.MediaStorageSOPInstanceUID = "1.2.3"
    # !!! Need valid UIDs here
    file_meta.ImplementationClassUID = "1.2.3.4"
    filename = '%s/%s.dcm' % (args.output, DS.SOPInstanceUID)
    ds = FileDataset(filename, {},
                     file_meta=file_meta, preamble="\0" * 128)
    ds.update(DS)
    #ds.is_little_endian = True
    #ds.is_implicit_VR = True
    ds.save_as(filename)
    print "File %s written" % filename

    # must return appropriate status
    return SOPClass.Success

# create application entity
MyAE = AE(args.aet, args.port, [PatientRootFindSOPClass,
                             PatientRootMoveSOPClass,
                             VerificationSOPClass], [StorageSOPClass], ts)
# AE class inherits from threading.Thread
# making it a daemon, will make it stop when the main thread stops
MyAE.daemon = True

MyAE.OnAssociateResponse = OnAssociateResponse
MyAE.OnAssociateRequest = OnAssociateRequest
MyAE.OnReceiveStore = OnReceiveStore
MyAE.start()

#def signal_handler(signal, frame):
#    print('You pressed Ctrl+C!')
#    MyAE.Quit()
#    sys.exit(0)

#signal.signal(signal.SIGINT, signal_handler)


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
#d.PatientsName = "*"
#d.PatientID = args.searchstring
d.SeriesInstanceUID = args.searchstring

items = list_pacs(d)

for i in items:
    print i
    copy_dicom(i)
 

# done
MyAE.Quit()
