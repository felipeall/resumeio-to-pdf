# Resume.io to PDF

Download your resume from [resume.io](https://resume.io) as a PDF file

<div align="center"><a href="https://resumeio-to-pdf.fly.dev/"><img src="https://user-images.githubusercontent.com/20917430/222932579-3cb4e5fe-9b9b-4a77-baf4-69e09ddc06d0.png" width="700" /></a></div>

### Usage
```bash
# Clone the repository
$ git clone https://github.com/felipeall/resumeio-to-pdf.git

# Go to the project's root folder
$ cd resumeio-to-pdf
```

#### Running in Docker
```bash
# Build the image
$ docker build -t resumeio-to-pdf .

# Run the container
$ docker run -p 8000:8000 resumeio-to-pdf
```

#### Running Locally

````bash
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
