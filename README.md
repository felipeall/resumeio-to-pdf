# Resume.io to PDF

Download your Résumé/CV from [resume.io](https://resume.io) as a PDF file

## Pre-requisites
1. CV created in [resume.io](https://resume.io)
2. Shareable link to the CV (e.g.: https://resume.io/r/VT0miU9jv)
3. Python environment

## Setup
````
$ git clone https://github.com/felipeall/resumeio-to-pdf.git
Cloning into 'resumeio-to-pdf'...

$ cd resumeio-to-pdf/
$ pip install -r requirements.txt
````

## Usage

````
python resumeio_to_pdf.py [resume_id | resume_url] [-q] [-h]
````

- `resume_id` (string): The ID extracted from the shareable link (e.g.: VT0miU9jv)
- `resume_url` (string): The full shareable URL to the CV (e.g.: https://resume.io/r/VT0miU9jv)
- `-q`: Quiet mode, suppress all console messages
- `-h`: Show the help message

## Examples

````
python resumeio_to_pdf.py -h
python resumeio_to_pdf.py VT0miU9jv
python resumeio_to_pdf.py VT0miU9jv -q
python resumeio_to_pdf.py https://resume.io/r/VT0miU9jv
python resumeio_to_pdf.py https://resume.io/r/VT0miU9jv -q
````
