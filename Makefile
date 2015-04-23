# Makefile for Sphinx documentation
# with additions for building pyds9
#
VERSION	      = 1.7

PYDS9	      = /proj/rd/www/pyds9
FTP	      = /proj/rd/ftp
TAR	      = pyds9-$(VERSION).tar.gz

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = $$HOME/python/bin/sphinx-build
PAPER         =

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d _build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help clean html dirhtml pickle json htmlhelp qthelp latex changes linkcheck doctest

# When changing documentation using sphinx-build:
#   documentation params are in conf.py (e.g. release version)
#   documentation markup is index.rst
# When making a new release, change version in setup.py and ds9.py

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  install   to install pyds9"
	@echo "  sdist     to make pyds9 source tar file"
	@echo "  html      to make standalone HTML files"
	@echo "  intallhtml to install HTML files in /proj/rd/www/ds9"
	@echo "  release   to run install, sdist, html, and installhtml"
	@echo "  -------------------- not used ------------------------"
	@echo "  dirhtml   to make HTML files named index.html in directories"
	@echo "  pickle    to make pickle files"
	@echo "  json      to make JSON files"
	@echo "  htmlhelp  to make HTML files and a HTML help project"
	@echo "  qthelp    to make HTML files and a qthelp project"
	@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  changes   to make an overview of all changed/added/deprecated items"
	@echo "  linkcheck to check all external links for integrity"
	@echo "  doctest   to run all doctests embedded in the documentation (if enabled)"

bclean:
	@rm -rf _build/*

clean:
	@(rm -f *~ foo*; cd xpa && make clean && cd ..;)	

release: clean install sdist html installhtml ftp

install:
	@python setup.py install --prefix=$$HOME/python

sdist:
	@python setup.py sdist

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) _build/html
	@echo
	@echo "Build finished. The HTML pages are in _build/html."

installhtml:
	@(echo skip rm -rf $(PYDS9);				\
	  mkdir -p $(PYDS9);  					\
	  chmod g+s $(PYDS9);  					\
	  cd _build/html;					\
	  tar cf - . | (cd $(PYDS9); tar xf -);			\
	)

ftp:
	@(cp -p dist/$(TAR) $(FTP);				\
	  chmod 444 dist/$(TAR)					\
	)

dirhtml:
	$(SPHINXBUILD) -b dirhtml $(ALLSPHINXOPTS) _build/dirhtml
	@echo
	@echo "Build finished. The HTML pages are in _build/dirhtml."

pickle:
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) _build/pickle
	@echo
	@echo "Build finished; now you can process the pickle files."

json:
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) _build/json
	@echo
	@echo "Build finished; now you can process the JSON files."

htmlhelp:
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) _build/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in _build/htmlhelp."

qthelp:
	$(SPHINXBUILD) -b qthelp $(ALLSPHINXOPTS) _build/qthelp
	@echo
	@echo "Build finished; now you can run "qcollectiongenerator" with the" \
	      ".qhcp project file in _build/qthelp, like this:"
	@echo "# qcollectiongenerator _build/qthelp/pyds9.qhcp"
	@echo "To view the help file:"
	@echo "# assistant -collectionFile _build/qthelp/pyds9.qhc"

latex:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) _build/latex
	@echo
	@echo "Build finished; the LaTeX files are in _build/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

changes:
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) _build/changes
	@echo
	@echo "The overview file is in _build/changes."

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) _build/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in _build/linkcheck/output.txt."

doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) _build/doctest
	@echo "Testing of doctests in the sources finished, look at the " \
	      "results in _build/doctest/output.txt."
