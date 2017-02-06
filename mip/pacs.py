from netdicom.applicationentity import AE
from netdicom.SOPclass import *
from dicom.dataset import Dataset, FileDataset
from dicom.UID import ExplicitVRLittleEndian, ImplicitVRLittleEndian, ExplicitVRBigEndian
import logging
import os
from datetime import datetime

class Pacs:
    def __init__(self,port=1234,
                    aet='ACME1',
                    aem='ACME1',
                    output='out',
                    implicit=None,
                    explicit=None):
        self.RemoteAE = None
        self.onDicomSaved = None
        self.import_folder = None
        self.logger = logging.getLogger(__name__)
        if implicit:
            ts = [ImplicitVRLittleEndian]
        elif explicit:
            ts = [ExplicitVRLittleEndian]
        else:
            ts = [
                ExplicitVRLittleEndian,
                ImplicitVRLittleEndian,
                ExplicitVRBigEndian
            ]
        self.port = port
        self.aet = aet
        self.aem = aem
        self.output = output
        self.MyAE = AE(aet, port, [StudyRootFindSOPClass,
                             StudyRootMoveSOPClass,
                             PatientRootFindSOPClass,
                             PatientRootMoveSOPClass,
                             VerificationSOPClass], [StorageSOPClass], ts)
        self.MyAE.OnAssociateResponse = self.OnAssociateResponse
        self.MyAE.OnAssociateRequest = self.OnAssociateRequest
        self.MyAE.OnReceiveStore = self.OnReceiveStore
      
    def connect(self, remotehost, remoteport, aec):
        self.RemoteAE = dict(Address=remotehost,Port=remoteport,AET=aec)
        self.logger.debug("starting local application entity")
        self.MyAE.start()
        # create association with remote AE
        try:
            self.logger.info("Requesting association")
            assoc = self.MyAE.RequestAssociation(self.RemoteAE)
            # perform a DICOM ECHO
            st = assoc.VerificationSOPClass.SCU(1)
        except:
            self.logger.critical("Unable to get association with %s, is the server running?" % self.RemoteAE)
            raise
        self.logger.info('done with status "%s"' % st)
        now = datetime.now()
        self.import_folder = os.path.join(self.output, now.strftime('%Y.%m.%d:%H:%M:%S'))
        assoc.Release(0)

    def OnAssociateResponse(self, association):
        self.logger.debug("Association response received")

    def OnAssociateRequest(self, association):
        self.logger.debug("Association resquested")
        return True

    def OnReceiveStore(self, SOPClass, ds):
        # do something with dataset. For instance, store it.
        self.logger.debug("Received C-STORE SeriesInstanceUID:'%s', SOPInstanceUID:'%s''" 
                    % (ds.SeriesInstanceUID, ds.SOPInstanceUID))
        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
        # !! Need valid UID herecopy_dicom
        file_meta.MediaStorageSOPInstanceUID = "1.2.3"
        # !!! Need valid UIDs here
        file_meta.ImplementationClassUID = "1.2.3.4"
        folder = os.path.join( self.import_folder, ds.StudyID)
        if not os.path.isdir(folder):
           os.makedirs(folder)
        filename = '%s/%s.dcm' % (folder, ds.SOPInstanceUID)
        fileds = FileDataset(filename, {},
                         file_meta=file_meta, preamble="\0" * 128)
        fileds.update(ds)
        fileds.save_as(filename)
        self.logger.info("file %s written" % filename)
        if self.onDicomSaved:
            self.logger.info("calling callback")
            self.onDicomSaved(filename)
        # must return appropriate status
        return SOPClass.Success

    def query(self, dataset):    
        assoc = self.MyAE.RequestAssociation(self.RemoteAE)
        st = assoc.StudyRootFindSOPClass.SCU(dataset, 1)
        items = [ss[1] for ss in st if ss[1]]
        assoc.Release(0)
        return items

    def list_studies(self):
        d = Dataset()
        d.QueryRetrieveLevel = "STUDY"
        d.SeriesInstanceUID = '*'
        return self.query(d)

    def copy_dicom(self, dataset):    
        assoc = self.MyAE.RequestAssociation(self.RemoteAE)
        gen = assoc.StudyRootMoveSOPClass.SCU(dataset, self.aem, 1)
        for gg in gen:
            # we have to access the item to copy it (it will be done asynchronously)
            self.logger.debug("copying %s" % gg)
            x = gg
        assoc.Release(0)

    def quit(self):
        self.MyAE.Quit()
