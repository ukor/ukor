FILE ?= default.md


.PHONY: help


help:
	@echo "Available commands:"
	@echo "  make all             - Runs the build (currently just echo)"
	@echo "  make create_article  - Creates a new article. Use FILE=\"my-article.md\" or get prompted."
	@echo "  make create_garden   - Creates a new digital garden note. Use FILE=\"my-note.md\" or get prompted."
	@echo "  make graph           - Generates the Hugo module graph."
	@echo "  make serve           - Starts the Hugo development server."
	@echo ""
	@echo "  To specify a filename: make create_article FILE=\"my-new-file.md\""


create_article:
	@echo "-----------"
	@echo "Creating content/articles/$(FILE)"
	@echo "-----------"
	hugo new content articles/"$(FILE)"


create_garden:
	@echo "-----------"
	@echo "Creating $(FILE) in content/digital-garden/$(FILE)"
	@echo "-----------"
	hugo mod graph
	hugo new content digital-garden/"$(FILE)"

graph:
	hugo mod graph
