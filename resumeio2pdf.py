import argparse
import json
import os
import requests
from datetime import datetime
from fpdf import FPDF


def _get_metadata(metadata_url: str):

    request = requests.get(metadata_url)
    metadata = json.loads(request.text)
    metadata = metadata.get('pages')

    return metadata

def _download_images(meta, resume_id, extension, cache_date, image_size, image_url):

    images_files = []

    for page_id in range(1, 1+len(meta)):
        page_file = f"{resume_id}-{page_id}.{extension}"
        download_url = image_url.format(resume_id, page_id, extension, cache_date, image_size)
        
        image_data = requests.get(download_url).content
        with open(page_file, 'wb') as handler:
            handler.write(image_data)

        images_files.append(page_file)
    
    return images_files

def _generate_pdf(meta, pages, pdfFileName):
    w, h = meta[0].get('viewport').values()

    pdf = FPDF(format=(w, h))
    pdf.set_auto_page_break(0)

    for i, page in enumerate(pages):
        pdf.add_page()
        pdf.image(page, w=w, h=h)

        for link in meta[i].get('links'):
            x = link['left']
            y = h - link['top']

            pdf.link(x=x, y=y, w=link['width'], h=link['height'], link=link['url'])
    
    pdf.output(pdfFileName, 'F')

def _cleanup(pages):

    for file in pages:
        os.remove(file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume_id', type=str, required=True)
    parser.add_argument('--extension', type=str, default='png')
    parser.add_argument('--image_size', type=int, default=1800)
    parser.add_argument('--cache_date', type=str, default=datetime.utcnow().isoformat()[:-4]+'Z')
    args = parser.parse_args()
    
    resume_id = args.resume_id
    extension = args.extension
    image_size = args.image_size
    cache_date = args.cache_date

    IMAGE_URL = "https://ssr.resume.tools/to-image/ssid-{0}-{1}.{2}?cache={3}&size={4}"
    METADATA_URL = f"https://ssr.resume.tools/meta/ssid-{resume_id}?cache={cache_date}"
    PDF_FILE_NAME = f"{resume_id}.pdf"

    meta = _get_metadata(METADATA_URL)
    pages = _download_images(meta, resume_id, extension, cache_date, image_size, IMAGE_URL)

    _generate_pdf(meta, pages, PDF_FILE_NAME)
    _cleanup(pages)
    

if __name__ == '__main__':
    main()
