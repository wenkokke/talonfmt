# Bump versions

patch:
	bumpver update --patch

minor:
	bumpver update --minor

major:
	bumpver update --major

.PHONY: patch minor major

# Publish to PyPi

PROJECT = "talonfmt"

CURRENT_VERSION = $(shell eval $$(bumpver show --no-fetch --env) && echo "$$CURRENT_VERSION")

CURRENT_WHEEL = dist/$(PROJECT)-$(CURRENT_VERSION)-py3-none-any.whl
CURRENT_TARGZ = dist/$(PROJECT)-$(CURRENT_VERSION).tar.gz

SOURCES = $(shell find $(PROJECT) -name "*.py")

$(CURRENT_WHEEL) $(CURRENT_TARGZ): $(SOURCES)
	pytest
	python -m build

testpublish: $(CURRENT_WHEEL) $(CURRENT_TARGZ)
	twine check $(CURRENT_WHEEL) $(CURRENT_TARGZ)
	twine upload -r testpypi $(CURRENT_WHEEL) $(CURRENT_TARGZ)
	touch testpublish

publish: $(CURRENT_WHEEL) $(CURRENT_TARGZ)
	twine check $(CURRENT_WHEEL) $(CURRENT_TARGZ)
	twine upload -r pypi $(CURRENT_WHEEL) $(CURRENT_TARGZ)
	touch publish
