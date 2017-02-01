import argparse
from netdicom.applicationentity import AE
from netdicom.SOPclass import *
from dicom.dataset import Dataset, FileDataset
from dicom.UID import ExplicitVRLittleEndian, ImplicitVRLittleEndian, \
    ExplicitVRBigEndian
import tempfile
import signal
import sys
from os import path
from datetime import datetime
import logging
from logging.config import fileConfig



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
parser.add_argument('-l','--log', help='configuration log file', default='logging.ini')
parser.add_argument('-C','--csv', help='csv file with the already processed dicoms', default='dicoms_processed.csv')
parser.add_argument('-e','--explicit', action='store_true',
                    help='negociate explicit transfer syntax only',
                    default=False)

args = parser.parse_args()

if path.isfile(args.log):
    fileConfig(args.log)
else:
    logging.warning("could not find configuration log file '%s'" % args.log)

logger = logging.getLogger()

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
    logger.debug("Association response received")


def OnAssociateRequest(association):
    logger.debug("Association resquested")
    return True

def OnReceiveStore(SOPClass, ds):
    # do something with dataset. For instance, store it.
    logger.debug("Received C-STORE SeriesInstanceUID:'%s', SOPInstanceUID:'%s''" 
                % (ds.SeriesInstanceUID, ds.SOPInstanceUID))
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
    fileds.save_as(filename)
    logger.info("file %s written" % filename)
    # must return appropriate status
    return SOPClass.Success

# create application entity
MyAE = AE(args.aet, args.port, [StudyRootFindSOPClass,
                             StudyRootMoveSOPClass,
                             VerificationSOPClass], [StorageSOPClass], ts)

logger.debug("creating application entity")
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
logger.debug("creating remote application entity")
RemoteAE = dict(Address=args.remotehost, Port=args.remoteport, AET=args.aec)

def list_pacs(dataset):    
    assoc = MyAE.RequestAssociation(RemoteAE)
    st = assoc.StudyRootFindSOPClass.SCU(dataset, 1)
    items = [ss[1] for ss in st if ss[1]]
    assoc.Release(0)
    return items

def copy_dicom(dataset):    
    assoc = MyAE.RequestAssociation(RemoteAE)
    gen = assoc.StudyRootMoveSOPClass.SCU(dataset, args.aem, 1)
    for gg in gen:
        # we have to access the item to copy it (it will be done asynchornously)
        logger.debug("copying %s" % gg)
        x = gg
    assoc.Release(0)

# create association with remote AE
logger.info("Requesting association")
assoc = MyAE.RequestAssociation(RemoteAE)
# perform a DICOM ECHO
st = assoc.VerificationSOPClass.SCU(1)
logger.info('done with status "%s"' % st)
assoc.Release(0)

d = Dataset()
d.QueryRetrieveLevel = "STUDY"
d.SeriesInstanceUID = '*'

processed = dict()
if path.isfile(args.csv):
    # opens the csv file with the already processed items
    with open(args.csv, "r") as f:
        # skips the header
        for line in f.readlines()[1:]:
            items = line.split(',')
            processed[items[0]]=items[1]
else:
    logger.warning('file "%s" with already processed dicoms not found, creating an empty one' % args.csv)
    # starts a new file
    with open(args.csv, "w") as f:
        f.write("SeriesInstanceUID,processed_date\n")

items = list_pacs(d)
# will update the file by append the new lines 
with open(args.csv, 'a') as csv_file:
    for i in items:
        if i.SeriesInstanceUID in processed:
            logger.info("Series already processed SeriesInstanceUID:" + i.SeriesInstanceUID)
        else:
            logger.info("found new series starting download")
            logger.info(i)
            # writes a new line in the csv file so that it remembers the next time
            csv_file.write("%s,%s\n" % (i.SeriesInstanceUID, datetime.now()))
            copy_dicom(i)
 
# done
MyAE.Quit()
