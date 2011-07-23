all:
	@echo "This is pure python, there is nothing to make."
	@echo "The Makefile is only here to automate development tasks."


PYLINT_FORMAT=$(shell [ "${INSIDE_EMACS}" = "t" ] && echo parseable || echo colorized )
PYLINT_OPT=--good-names=i,j,k,s,p,o,ex,Run,_,kw,id --output-format=${PYLINT_FORMAT} --ignore=iso8601.py --ignore-docstrings=no
PYLINT_DISABLED=--disable="I0011,W0142,W0511,R0901,R0912,R0913,R0914,R0915,R0921"
PYLINT_FILES=lib/rdfrest lib/ktbs

lint-full:
	@PYTHONPATH=lib pylint ${PYLINT_FILES} ${PYLINT_OPT}

lint-todos:
	@PYTHONPATH=lib pylint ${PYLINT_FILES} ${PYLINT_OPT} ${PYLINT_DISABLED} --report=n --enable=W0511 | grep 'MAJOR\|^' --color

lint:
	@PYTHONPATH=lib pylint ${PYLINT_FILES} ${PYLINT_OPT} ${PYLINT_DISABLED} --report=n --include-ids=y

unit-tests:
	@PYTHONPATH=lib nosetests utest
