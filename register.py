import pandoc
import os

def markdown_to_rst(src):
  pandoc.core.PANDOC_PATH = '/usr/local/bin/pandoc'

  doc = pandoc.Document()
  doc.markdown = open('README.md').read()
  return doc.rst
