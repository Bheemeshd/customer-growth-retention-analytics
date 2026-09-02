PYTHON ?= python3

.PHONY: setup data pipeline test dashboard all

setup:
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) -m src.generate_data

pipeline:
	$(PYTHON) -m src.pipeline

test:
	$(PYTHON) -m unittest discover -s tests -v

dashboard:
	$(PYTHON) -m streamlit run app/dashboard.py

all: data pipeline test

