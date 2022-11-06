import argparse
import json
import requests
from datetime import datetime
from fpdf import FPDF


def _get_resume_metadata(metadata_url: str, resume_id: str, cache_date: str):

    request = requests.get(metadata_url.format(resume_id, cache_date))
    metadata = json.loads(request.text)
    metadata = metadata.get('pages')

    return metadata

def _format_images_urls(metadata: list[dict], resume_id: str, extension: str, cache_date: str, image_size: int, image_url: str):

    images_urls = []

    for page_id in range(1, 1+len(metadata)):
        download_url = image_url.format(resume_id, page_id, extension, cache_date, image_size)
        images_urls.append(download_url)
    
    return images_urls

def _generate_pdf(metadata: list[dict], images_urls: list, resume_id: str, extension: str):
    pdf_file_name = f"{resume_id}.pdf"
    w, h = metadata[0].get('viewport').values()

    pdf = FPDF(format=(w, h))
    pdf.set_auto_page_break(0)

    for i, image_url in enumerate(images_urls):
        pdf.add_page()
        pdf.image(image_url, w=w, h=h, type=extension)

        for link in metadata[i].get('links'):
            x = link['left']
            y = h - link['top']

            pdf.link(x=x, y=y, w=link['width'], h=link['height'], link=link['url'])
    
    pdf.output(pdf_file_name, 'F')


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
    METADATA_URL = "https://ssr.resume.tools/meta/ssid-{0}?cache={1}"

    metadata = _get_resume_metadata(METADATA_URL, resume_id, cache_date)
    images_urls = _format_images_urls(metadata, resume_id, extension, cache_date, image_size, IMAGE_URL)

    _generate_pdf(metadata, images_urls, resume_id, extension)
    

if __name__ == '__main__':
    main()
