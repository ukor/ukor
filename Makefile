FILE ?= default.md


.PHONY: all

all:
	@echo "Running build..."

create_article:
	@echo "-----------"
	@echo "Creating $(FILE) in content/articles"
	@echo "-----------"
	hugo new content articles/"$(FILE)"


create_garden:
	@echo "-----------"
	@echo "Creating $(FILE) in content/digital-garden"
	@echo "-----------"
	hugo mod graph
	hugo new content digital-garden/"$(FILE)"

graph:
	hugo mod graph
