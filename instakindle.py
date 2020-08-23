import requests
from readability import Document
from lxml import etree
from io import StringIO
from sys import argv
from ebooklib import epub
from urllib.parse import urlparse


def fetch_content(url):
    resp = requests.get(url)
    return resp.text


def simplify_content(text):
    return Document(text)


def parse_html(text):
    parser = etree.HTMLParser()
    return etree.parse(StringIO(text), parser)


def get(url):
    doc = simplify_content(fetch_content(url))
    tree = parse_html(doc.summary())
    return (doc, tree)


def get_html_content(tree):
    return etree.tostring(tree.getroot(), pretty_print=True, method="html")


def get_filename_from_url(url):
    parsed_url = urlparse(url)
    return parsed_url.path.rpartition('/')[-1]


def build_chapter(doc, tree):
    chapter = epub.EpubHtml(
        title=doc.title(), file_name='chapter.xhtml', lang='en')

    images = []

    # we need to download all the images, create image items for them, and
    # add them to the chapter
    for i, image in enumerate(tree.iter('img')):
        resp = requests.get(image.get('src'))
        filename = f'images/{get_filename_from_url(resp.url)}'

        image_item = epub.EpubItem(uid=f'image{i}', file_name=filename,
                                   media_type=resp.headers['Content-Type'], content=resp.content)

        images.append(image_item)

        image.set('src', filename)

    chapter.set_content(get_html_content(tree))

    return (chapter, images)


def write_epub(doc, tree):
    book = epub.EpubBook()

    book.set_identifier('samplebook')  # what should this be?
    book.set_title(doc.title())
    book.set_language('en')

    book.add_author('instakindle')

    chapter, images = build_chapter(doc, tree)

    book.add_item(chapter)

    for image in images:
        book.add_item(image)

    book.spine = [chapter]
    book.toc = [chapter]

    # book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(f'{doc.title()}.epub', book)


def write_content(doc, tree):
    with open(f'{doc.title()}.html', 'wb') as f:
        f.write()


if __name__ == "__main__":
    if len(argv) >= 2:
        doc, tree = get(argv[1])

        # write_content(doc, tree)

        write_epub(doc, tree)
