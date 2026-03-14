.PHONY: major minor patch

PYPROJECT := pyproject.toml
INIT_FILE := src/panda_cli/__init__.py

# Читаем текущую версию из pyproject.toml
CURRENT := $(shell grep '^version = ' $(PYPROJECT) | sed 's/version = "\(.*\)"/\1/')
MAJOR   := $(shell echo $(CURRENT) | cut -d. -f1)
MINOR   := $(shell echo $(CURRENT) | cut -d. -f2)
PATCH   := $(shell echo $(CURRENT) | cut -d. -f3)

define bump
	@echo UPDATED "$(CURRENT) → $(1)"
	@sed -i 's/^version = ".*"/version = "$(1)"/' $(PYPROJECT)
	@sed -i 's/^__version__ = ".*"/__version__ = "$(1)"/' $(INIT_FILE)
endef

major:
	$(call bump,$(shell echo $$(($(MAJOR)+1))).0.0)

minor:
	$(call bump,$(MAJOR).$(shell echo $$(($(MINOR)+1))).0)

patch:
	$(call bump,$(MAJOR).$(MINOR).$(shell echo $$(($(PATCH)+1))))