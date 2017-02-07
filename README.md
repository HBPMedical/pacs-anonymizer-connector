# pacs-anonymizer-connector

Simple python script to download files from a PACS system and anonymize them using gnubila's anonymizer in one go.
It is here just as an alternative to using a tomcat server.
## Installing Dependencies
It needs pydicom and pynedicom:

`pip install git+https://github.com/darcymason/pydicom.git`

`pip install git+https://github.com/torcato/pynetdicom.git`

## Downloading all dicoms files from a pacs
example:

`python pacs_anonymize.py -o out/ --aet HBP --aec COMMON -D localhost 11112`

Your local port `port`, aet, aec have to be in the configuration of your PACS system or it will be refused.
For now it uses a csv file where it stores all the already copyed files, so if you re-run this script it might not download and anonymize anything (if there is no new data).

###List of command line arguments
--help will also print this information

positional arguments:

  n  | arguments          | Description
---- | ------------------ | ---
1    |remotehost          |PACS hostname   
2    |remoteport          |PACS port   

optional arguments:

 argument| description
  ------ | ---------- 
-h, --help                                     | show this help message and exit            
-p PORT, --port PORT                           | local server port                          
-t AET, --aet AET                              | calling AET title                          
-c AEC, --aec AEC                              | calling AEC call, the data-store to access
-i, --implicit                                 | negociate implicit transfer syntax only    
-e, --explicit                                 | negociate explicit transfer syntax only    
-o OUTPUT, --output OUTPUT                     | output folder to save the dicom files      
-l LOG, --log LOG                              | configuration log file                     
-C CSV, --csv CSV                              | csv file with the already processed dicoms 
-J ANON, --anonymizer-jar ANON                 | path for the jar file of the anonymiser    
-S SCRIPT, --dicom-script SCRIPT               | dicom script for anonymizer                
-Q QUARANTINE, --quarantine QUARANTINE         | Anonymizer quarantine folder               
-T LOOKUP_TABLE, --lookup-table LOOKUP_TABLE   | Anonymizer lookup table   
-D, --download-only                            | Download dicoms only, without anonymization
