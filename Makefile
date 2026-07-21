PY ?= venv/bin/python
NOTE ?= AI command-center health run.
SLIDES ?= 5
PHASE ?= all
MAX_ITERATIONS ?= 12
STAGNATION_LIMIT ?= 3
IDEA_MAX_ITERATIONS ?= 3
IDEA_CANDIDATES ?= 6

.PHONY: help brief health wiki-health idea-loop jam prepost carousel visual-check review-loop article publish publish-dry-run test

help:
	@printf "%s\n" "AI command center commands:"
	@printf "%s\n" "  make brief                       Show today's creator/engineering brief"
	@printf "%s\n" "  make health NOTE='...'           Run wiki/memory health with write + index fix"
	@printf "%s\n" "  make idea-loop                   Discover and verify one fresh Instagram idea"
	@printf "%s\n" "  make jam MOMENT='...'            Prepare a carousel jam prompt/command"
	@printf "%s\n" "  make prepost CONCEPT='...'       Run planned Reel pre-post analysis"
	@printf "%s\n" "  make carousel STORY='...'        Create a carousel package"
	@printf "%s\n" "  make visual-check CAROUSEL=path  Check directed story before/after imagegen"
	@printf "%s\n" "  make review-loop CAROUSEL=path   Review, repair, and recheck until clean or honestly blocked"
	@printf "%s\n" "  make article CAROUSEL=path       Create Substack article package"
	@printf "%s\n" "  make publish NOTE='...'          Run safe verify -> commit -> push gate"
	@printf "%s\n" "  make publish-dry-run NOTE='...'  Preview safe publish scope"
	@printf "%s\n" "  make test                        Run the local test suite"

brief:
	$(PY) scripts/daily_creator_brief.py

health wiki-health:
	$(PY) scripts/run_content_health.py --session-note "$(NOTE)"

idea-loop:
	$(PY) scripts/instagram_idea_loop.py run $(if $(SEED),--seed "$(SEED)") --max-iterations "$(IDEA_MAX_ITERATIONS)" --candidate-budget "$(IDEA_CANDIDATES)" $(if $(RUN_DIR),--run-dir "$(RUN_DIR)") $(if $(DRY_RUN),--dry-run) $(if $(LIVE_SEARCH),--live-search)

jam:
	$(PY) scripts/jam_today.py $(if $(MOMENT),--moment "$(MOMENT)") --slides "$(SLIDES)"

prepost:
	$(PY) scripts/analyze_prepost.py $(if $(CONCEPT),--concept "$(CONCEPT)") $(if $(HOOK),--hook "$(HOOK)") $(if $(CAPTION),--caption "$(CAPTION)") $(if $(EDIT),--edit "$(EDIT)") $(if $(AUDIO),--audio "$(AUDIO)") $(if $(COVER),--cover "$(COVER)")

carousel:
	$(PY) -m pytest tests/test_agentic_docs_contract.py tests/test_instruction_surface_contract.py tests/test_codex_project_surfaces.py tests/test_creator_workflow_contract.py -q
	$(PY) -m pytest tests/test_checks_prompt_constraints.py tests/test_checks_image_size.py tests/test_carousel_state_contract.py tests/test_carousel_workflow_doctor.py tests/test_carousel_doctor_cli.py -q
	$(PY) scripts/agentic_os.py health
	$(PY) scripts/create_illustration_carousel.py $(if $(STORY),--story "$(STORY)") $(if $(TITLE),--title "$(TITLE)") --slide-count "$(SLIDES)" $(foreach image,$(IMAGE),--image "$(image)") $(foreach identity,$(IDENTITY_IMAGE),--identity-image "$(identity)")

visual-check:
	@test -n "$(CAROUSEL)" || (printf "%s\n" "Usage: make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=pre|post|all"; exit 2)
	$(PY) .agents/skills/a-story-direct-visual-story/scripts/check_visual_story.py --carousel-dir "$(CAROUSEL)" --phase "$(PHASE)"

review-loop:
	@test -n "$(CAROUSEL)" || (printf "%s\n" "Usage: make review-loop CAROUSEL=output/carousels/YYYY-MM-DD/slug [MAX_ITERATIONS=12] [REPAIR_COMMAND='...'] [VERIFY='...']"; exit 2)
	$(PY) scripts/carousel_review_loop.py "$(CAROUSEL)" --max-iterations "$(MAX_ITERATIONS)" --stagnation-limit "$(STAGNATION_LIMIT)" $(if $(REPAIR_COMMAND),--repair-command "$(REPAIR_COMMAND)") $(if $(VERIFY),--verify-command "$(VERIFY)")

article:
	@test -n "$(CAROUSEL)" || (printf "%s\n" "Usage: make article CAROUSEL=output/carousels/YYYY-MM-DD/slug TITLE='Optional title'"; exit 2)
	$(PY) scripts/create_substack_article_package.py --carousel-dir "$(CAROUSEL)" $(if $(TITLE),--title "$(TITLE)")

publish:
	$(PY) scripts/autopublish.py --session-note "$(NOTE)" $(foreach include,$(INCLUDE),--include "$(include)") $(if $(NO_PUSH),--no-push)

publish-dry-run:
	$(PY) scripts/autopublish.py --dry-run --session-note "$(NOTE)" $(foreach include,$(INCLUDE),--include "$(include)") $(if $(NO_PUSH),--no-push)

test:
	$(PY) -m pytest
