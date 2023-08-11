# Resume.io to PDF

Download your Resume/CV from [resume.io](https://resume.io) as a PDF file

### Deployed Application

> [resumeio-to-pdf.vercel.app](https://resumeio-to-pdf.vercel.app/)

<div align="center"><a href="https://resumeio-to-pdf.vercel.app/"><img src="https://user-images.githubusercontent.com/20917430/222932579-3cb4e5fe-9b9b-4a77-baf4-69e09ddc06d0.png" width="700" /></a></div>


### Running Locally

````bash
# Clone the repository
$ git clone https://github.com/felipeall/resumeio-to-pdf.git

# Go to the project's root folder
$ cd resumeio-to-pdf

# (optional) Append the current directory to PYTHONPATH
$ export PYTHONPATH=$PYTHONPATH:$(pwd)

# Instantiate a Poetry virtual env
$ poetry shell

# Install the dependencies
$ poetry install

# Start the API server
$ python app/main.py
````
The application will be running in: [http://localhost:8000/](http://localhost:8000/)
