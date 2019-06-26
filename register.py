import pandoc
import os


def markdown_to_rst(src):
    pandoc.core.PANDOC_PATH = "/usr/local/bin/pandoc"
    if not os.path.exists(pandoc.core.PANDOC_PATH):
        raise Exception("Pandoc not available")

    doc = pandoc.Document()
    doc.markdown = open("README.md").read()
    return doc.rst
