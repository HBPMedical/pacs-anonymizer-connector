import argparse
from os import path
from datetime import datetime
import logging
from logging.config import fileConfig
import tempfile
from dicom.dataset import Dataset

from mip import Pacs, DicomAnonymizer

# parse commandline
parser = argparse.ArgumentParser(description='Download and anonymize files from a PACS system')
#--------------- PACS options ------------------
parser.add_argument('remotehost')
parser.add_argument('remoteport', type=int)
parser.add_argument('-p', '--port', help='local server port', type=int, default=1234)
parser.add_argument('-t','--aet', help='calling AET title', default='HBP')
parser.add_argument('-c','--aec', help='calling AEC call, the data-store', default='COMMON')
parser.add_argument('-i','--implicit', action='store_true',
                    help='negociate implicit transfer syntax only',
                    default=False)
parser.add_argument('-e','--explicit', action='store_true',
                    help='negociate explicit transfer syntax only',
                    default=False)
parser.add_argument('-o','--output', help='output folder', default=tempfile.gettempdir())
parser.add_argument('-l','--log', help='configuration log file', default='logging.ini')
parser.add_argument('-C','--csv', help='csv file with the already processed dicoms', default='dicoms_processed.csv')
#----------- Anonymizer options ----------------
parser.add_argument('-D', '--download-only', 
                    help='Download dicoms only, without anonymization', 
                    action='store_true', default=False)
parser.add_argument('-J', '--anonymizer-jar', help='path for the jar file of the anonymiser', 
            default='../anonymizer/pandora-clients-fedehr-anonymiser-packaging-targz-1.0.0/lib/pandora-clients-fedehr-anonymiser-cli-1.0.0.jar')
parser.add_argument('-S', '--dicom-script', help='dicom script for anonymizer', default='dicom-scripts/DICOM-PS3.15-Basic')
parser.add_argument('-Q', '--quarantine', help='Anonymizer quarantine folder', default='quarantine')
parser.add_argument('-T', '--lookup-table', help='Anonymizer lookup table', default=None)


args = parser.parse_args()

if path.isfile(args.log):
    fileConfig(args.log)
else:
    logging.warning("could not find configuration log file '%s'" % args.log)

logger = logging.getLogger(__name__)

#starts our pacs instance
pacs = Pacs( args.port,
            args.aet,
            args.output,
            args.implicit,
            args.explicit)

if not args.download_only:
    anon = DicomAnonymizer(args.anonymizer_jar, args.quarantine, args.dicom_script, args.lookup_table)
    # sets te callback when storing a file to anonymize it
    pacs.onDicomSaved = anon.anonymize

pacs.connect(args.remotehost, 
            args.remoteport, 
            args.aec)

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

items = pacs.list_studies()
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
            pacs.copy_dicom(i)
 
# done
pacs.quit()
