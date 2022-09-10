build:
	poetry build

clean:
	@git clean -dfqX

bump-patch:
	@poetry install --with dev
	@poetry run bumpver update --patch

bump-minor:
	@poetry install --with dev
	@poetry run bumpver update --minor

bump-major:
	@poetry install --with dev
	@poetry run bumpver update --major

.PHONY: build clean test bump-patch bump-minor bump-major
