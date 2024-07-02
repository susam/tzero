help:
	@echo 'Usage: make [target]'
	@echo
	@echo 'Development Targets:'
	@echo '  venv      Create virtual Python environment for development.'
	@echo '  checks    Run linters and tests.'
	@echo
	@echo 'Deployment Targets:'
	@echo '  service   Remove, install, configure, and run app.'
	@echo '  rm        Remove app.'
	@echo '  help      Show this help message.'


# Development Targets
# -------------------

VENV = ~/.venv/tzero

venv: FORCE
	rm -rf $(VENV)/
	python3 -m venv $(VENV)/
	$(VENV)/bin/pip3 install -U build twine
	$(VENV)/bin/pip3 install ruff mypy

lint:
	$(VENV)/bin/ruff check
	$(VENV)/bin/ruff format --diff
	$(VENV)/bin/mypy .

test:
	$(VENV)/bin/python3 -m unittest -v

coverage:
	$(VENV)/bin/coverage run --branch -m unittest -v
	$(VENV)/bin/coverage report --show-missing
	$(VENV)/bin/coverage html

check-password:
	! grep -r '"password":' . | grep -vE '^\./[^/]*.json|Makefile|\.\.\.'

checks: lint test check-password

clean:
	rm -rf *.pyc __pycache__
	rm -rf .coverage htmlcov
	rm -rf dist tzero.egg-info


# Distribution Targets
# --------------------

dist: clean
	$(VENV)/bin/python3 -m build
	$(VENV)/bin/twine check dist/*
	unzip -c dist/*.whl '*/METADATA'
	unzip -t dist/*.whl
	tar -tvf dist/*.tar.gz

upload:
	$(VENV)/bin/twine upload dist/*

test-upload:
	$(VENV)/bin/twine upload --repository testpypi dist/*

UVENV = ~/.venv/user-tzero

user-venv: FORCE
	rm -rf $(UVENV)
	python3 -m venv $(UVENV)

verify-upload:
	$(MAKE) verify-sdist
	$(MAKE) verify-bdist

verify-test-upload:
	$(MAKE) verify-test-sdist
	$(MAKE) verify-test-bdist

verify-sdist: user-venv
	$(UVENV)/pip3 install --no-binary :all: tzero
	$(UVENV)/command -v tzero
	ls -l $(UVENV)/bin/tzero

verify-bdist: user-venv
	$(UVENV)/pip3 install tzero
	$(UVENV)/command -v tzero
	ls -l $(UVENV)/bin/tzero

verify-test-sdist: user-venv
	$(UVENV)/bin/pip3 install \
	  --index-url https://test.pypi.org/simple/ \
	  --extra-index-url https://pypi.org/simple \
	  --no-binary :all: \
	  --pre tzero
	ls -l $(UVENV)/bin/tzero

verify-test-bdist: user-venv
	$(UVENV)/bin/pip3 install \
	  --index-url https://test.pypi.org/simple/ \
	  --extra-index-url https://pypi.org/simple \
	  --pre tzero
	ls -l $(UVENV)/bin/tzero

# Deployment Targets
# ------------------

service: rmservice
	adduser --system --group --home / tzero
	mkdir -p /opt/data/tzero/
	chown -R tzero:tzero . /opt/data/tzero/
	chmod 600 tzero.json
	systemctl enable "$$PWD/etc/tzero.service"
	systemctl daemon-reload
	systemctl start tzero
	@echo Done; echo

rmservice:
	-systemctl stop tzero
	-systemctl disable tzero
	systemctl daemon-reload
	-deluser tzero
	@echo Done; echo

pull-backup:
	mkdir -p ~/bkp/
	ssh splnx.net "tar -czf - -C /opt/data/ tzero/" > ~/bkp/tzero-$$(date "+%Y-%m-%d_%H-%M-%S").tgz
	ls -lh ~/bkp/

FORCE:
