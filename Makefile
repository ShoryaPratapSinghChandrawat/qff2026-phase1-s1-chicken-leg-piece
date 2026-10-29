.PHONY: verify test notebook regenerate-stage-b

verify:
	python verify_submission.py

test:
	python -m pytest -q

notebook:
	jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 main.ipynb

# Regenerate the complete Stage B noise/resource outputs, including the final
# nine-row resource table, then fail if the submission verifier finds an issue.
regenerate-stage-b:
	python src/finish_stage_b.py
	python src/compare_processor_p2.py
	python verify_submission.py
