from mip import DicomAnonymizer

anon_exec = '../anonymizer/pandora-clients-fedehr-anonymiser-packaging-targz-1.0.0/lib/pandora-clients-fedehr-anonymiser-cli-1.0.0.jar'
anon_config = '../anonymizer/dicom-scripts/DICOM-PS3.15-Basic'
quarantine = '/tmp/quarantine'

anon = DicomAnonymizer(anon_exec, quarantine, anon_config)
anon.anonymize('/tmp/pacs/1.2.840.113619.2.284.3.1771772990.589.1365425464.595.140.dcm')
