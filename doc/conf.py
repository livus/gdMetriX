# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


import os
import sys

project = 'gdMetriX'
copyright = '2024, Martin Nöllenburg, Sebastian Röder, Markus Wallinger'
author = 'Martin Nöllenburg, Sebastian Röder, Markus Wallinger'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'nbsphinx', 'sphinx.ext.mathjax', 'sphinxcontrib.bibtex']

bibtex_bibfiles = ['references.bib']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"
html_static_path = ['_static']
html_logo = "_static/logo_dark.svg"
html_show_sourcelink = False
html_theme_options = {
    "use_edit_page_button": False,
    "show_prev_next": False,
    "logo": {
        "image_light": "_static/logo.svg",
        "image_dark": "_static/logo_dark.svg",
    }
}

sys.path.insert(0, os.path.abspath(os.path.join('..', 'src', 'gdMetriX')))
sys.path.insert(0, os.path.abspath(os.path.join('..', 'src')))
