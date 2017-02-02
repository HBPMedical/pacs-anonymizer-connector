# pacs-anonymizer-connector

Simple python script to download files from a PACS system and anonymize them using gnubila's anonymizer in one go.
It is here just as an alternative to using a tomcat server.
## Installing Dependencies
It needs pydicom and pynedicom:

`pip install pydicom`

`pip install git+https://github.com/torcato/pynetdicom`

## Usage
It is not completely finished, some more python scripts will be added.

### Copying all files from a PACS system

example:
`pacs_copy.py --port 1234 --aet ACME1 --aec COMMON --aem ACME1 -o out/ localhost 11112`

Your local port `port`, aet, aem have to be in the configuration of your PACS system or it will be refused
For now it uses a csv file where it stores all the already copyed files, so if you re-run this script it might not copy anything (if there is no new data).
