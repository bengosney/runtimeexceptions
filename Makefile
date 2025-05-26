.PHONY: help clean test install all init dev css watch node js clean-pyc
.DEFAULT_GOAL := install
.PRECIOUS: requirements.%.in

HOOKS=$(.git/hooks/pre-commit)
REQS=$(shell python -c 'import tomllib;[print(f"requirements.{k}.txt") for k in tomllib.load(open("pyproject.toml", "rb"))["project"]["optional-dependencies"].keys()]')

BINPATH=$(shell which python | xargs dirname | xargs realpath --relative-to=".")
DBTOSQLPATH=$(BINPATH)/db-to-sqlite

PYTHON_VERSION:=$(shell cat .python-version)
PIP_PATH:=$(BINPATH)/pip
WHEEL_PATH:=$(BINPATH)/wheel
PRE_COMMIT_PATH:=$(BINPATH)/pre-commit
UV_PATH:=$(BINPATH)/uv

PYTHON_FILES:=$(wildcard ./**/*.py ./**/tests/*.py)

STATIC_DIR:= static

STATIC_CSS_DIR:= $(STATIC_DIR)/css
CSS_FILES:= $(wildcard ./css/*.css ./css/**/*.css)

STATIC_JS_DIR:= $(STATIC_DIR)/js
JS_FILES:= $(wildcard ./js/*.js ./js/**/*.js)

check_command = @command -v $(1) >/dev/null 2>&1 || { echo >&2 "$(1) is not installed."; $(2); }

help: ## Display this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.git:
	git init

.pre-commit-config.yaml: | $(PRE_COMMIT_PATH) .git
	curl https://gist.githubusercontent.com/bengosney/4b1f1ab7012380f7e9b9d1d668626143/raw/060fd68f4c7dec75e8481e5f5a4232296282779d/.pre-commit-config.yaml > $@
	pre-commit autoupdate

requirements.%.txt: $(UV_PATH) requirements.txt pyproject.toml
	@echo "Builing $@"
	python -m uv pip compile --quiet --generate-hashes -o $@ --extra $* $(filter-out $<,$^)

requirements.txt: $(UV_PATH) pyproject.toml
	@echo "Builing $@"
	python -m uv pip compile --quiet --generate-hashes -o $@ $(filter-out $<,$^)

.direnv: .envrc
	python -m pip install --upgrade pip
	python -m pip install wheel pip-tools
	@touch $@ $^

.git/hooks/pre-commit: $(PRE_COMMIT_PATH) .pre-commit-config.yaml .git
	pre-commit install

.envrc:
	@echo "Setting up .envrc then stopping"
	@echo "layout python python$(PYTHON_VERSION)" > $@
	@touch -d '+1 minute' $@
	@false

$(WHEEL_PATH): $(PIP_PATH)
	python -m pip install wheel
	@touch $@

$(UV_PATH): $(PIP_PATH) $(WHEEL_PATH)
	python -m pip install uv
	@touch $@

$(PRE_COMMIT_PATH): $(PIP_PATH) $(WHEEL_PATH)
	python -m pip install pre-commit
	@touch $@

init: .direnv $(UV_PATH) .git .git/hooks/pre-commit requirements.txt requirements.dev.txt ## Initalise a enviroment

clean-pyc: ## Remove all python build files
	find . -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

clean: clean-pyc ## Remove all build files
	rm -f .testmondata
	rm -rf .hypothesis
	rm -rf .*cache
	rm -f .coverage
	find . -type d -empty -delete

package-lock.json: package.json
	npm install

node_modules: package.json package-lock.json
	npm install
	@touch $@

node: node_modules

python: $(UV_PATH) requirements.txt $(REQS)
	@echo "Installing $(filter-out $<,$^)"
	@python -m uv pip sync $(filter-out $<,$^)

update-template: $(UV_PATH) ## Update the template used to generate the project
	$(UV_PATH) tool run copier update -A

install: python node ## Install development requirements (default)

upgrade: python
	@echo "Updateing module paths"
	wagtail updatemodulepaths --ignore-dir .direnv
	python -m pre_commit autoupdate

cov.xml: $(PYTHON_FILES)
	python3 -m pytest --cov=. --cov-report xml:$@

coverage: $(PYTHON_FILES)
	python3 -m pytest --cov=. --cov-report html:$@

_server:
	python3 ./manage.py migrate
	python3 ./manage.py runserver

dev: _server watch-js watch-css bs ## Start the dev server, watch the css and js and start browsersync

infrastructure:
	git clone https://github.com/bengosney/tofu-wagtail.git $@
	cd $@ && $(MAKE) init

$(STATIC_CSS_DIR)/%.css: css/%.css  $(CSS_FILES) node_modules
	node_modules/.bin/postcss $< -o $@

css: $(STATIC_CSS_DIR)/main.css ## Compile the css files into a single file
