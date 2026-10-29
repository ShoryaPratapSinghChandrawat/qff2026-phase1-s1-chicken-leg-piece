.PHONY: verify test notebook

verify:
	python verify_submission.py

test:
	python -m pytest -q

notebook:
	jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 main.ipynb
