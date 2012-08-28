all:
	@echo "This is pure python, there is nothing to make."
	@echo "The Makefile is only here to automate development tasks."

PYPATH=PYTHONPATH=lib:example1
PYLINT_FORMAT=$(shell [ "${INSIDE_EMACS}" = "t" ] && echo parseable || echo colorized )
PYLINT_OPT=--good-names=g,i,j,k,s,p,o,ex,Run,_,kw,id --output-format=${PYLINT_FORMAT} --ignore=iso8601.py --ignore-docstrings=no
PYLINT_DISABLED=--disable="I0011,W0142,W0223,W0511,R0901,R0904,R0912,R0913,R0914,R0915,R0921,R0922,E1103"
PYLINT_FILES=rdfrest ktbs bin/ktbs bin/simple-collector utest.example1 utest.example2

lint-full:
	@${PYPATH} pylint ${PYLINT_FILES} ${PYLINT_OPT}

lint-todos:
	@${PYPATH} pylint ${PYLINT_FILES} ${PYLINT_OPT} ${PYLINT_DISABLED} --report=n --enable=W0511 | grep 'NOW\|^' --color

lint:
	@${PYPATH} pylint ${PYLINT_FILES} ${PYLINT_OPT} ${PYLINT_DISABLED} --report=n --include-ids=y

unit-tests:
	@${PYPATH} nosetests utest

doc-rdfrest:
	@cd doc-rdfrest; make html 2>&1
doc:
	@cd doc; make html 2>&1

.PHONY: lint-full lint-todos lint unit-tests doc doc-rdfrest
