PY ?= python
DB ?= warehouse/credit.duckdb
DBT_BIN ?= dbt
DBT = cd dbt && DUCKDB_PATH=../$(DB) $(DBT_BIN)
UCI = https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip

.PHONY: all download load features model ecl test clean

all: download load features model ecl test   ## real UCI data -> features -> PD model -> IFRS 9 ECL -> tests

download:   ## 5.5 MB from the UCI repository, no sign-in (CC BY 4.0)
	mkdir -p data/raw
	curl -sL -o data/raw/dccc.zip "$(UCI)"

load:
	$(PY) ingestion/load.py --zip data/raw/dccc.zip --db $(DB)

features:   ## dbt: staging, client x month panel, behavioural features
	$(DBT) deps --profiles-dir .
	$(DBT) build --profiles-dir . --exclude tag:ecl

model:      ## scorecard + challenger, validation, fairness check; writes ml.client_pd
	$(PY) model/train.py --db $(DB) --out results

ecl:        ## dbt: IFRS 9 staging, scenario-weighted ECL, transitions, sensitivities
	$(DBT) build --profiles-dir . --select tag:ecl

test:
	CREDIT_DB=$(DB) $(PY) -m pytest -q tests

clean:
	rm -rf warehouse dbt/target dbt/logs dbt/dbt_packages
