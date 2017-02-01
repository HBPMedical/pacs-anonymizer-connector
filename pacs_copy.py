import argparse
from os import path
from datetime import datetime
import logging
from logging.config import fileConfig
from dicom.dataset import Dataset
from mip import Pacs
import tempfile

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

#starts our pacs instance
pacs = Pacs( args.remotehost, 
            args.remoteport, 
            args.port,
            args.aet, 
            args.aem, 
            args.aec, 
            args.implicit, 
            args.explicit, 
            args.output)


# this is to force a quit on ctrl-c (sigint)
# the extra thread created to receive dicoms is not killed automatically
def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    pacs.quit()
    sys.exit(0)

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
