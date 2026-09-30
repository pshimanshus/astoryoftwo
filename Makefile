PY ?= $(firstword $(wildcard venv/bin/python ../../venv/bin/python))
ifeq ($(strip $(PY)),)
PY := python3
endif
NOTE ?= AI command-center health run.
PHASE ?= all
IDEA_MAX_ITERATIONS ?= 3
IDEA_CANDIDATES ?= 6
FEEDBACK_INTEGRATIONS_VENV ?= .venv-evals
FEEDBACK_INTEGRATIONS_PY ?= $(if $(wildcard $(FEEDBACK_INTEGRATIONS_VENV)/bin/python),$(FEEDBACK_INTEGRATIONS_VENV)/bin/python,$(PY))
export ASOT_IDEA_LOOP_SEED := $(value SEED)
export ASOT_IDEA_LOOP_RUN_DIR := $(value RUN_DIR)
export ASOT_IDEA_LOOP_MAX_ITERATIONS := $(value IDEA_MAX_ITERATIONS)
export ASOT_IDEA_LOOP_CANDIDATES := $(value IDEA_CANDIDATES)

.PHONY: help brief analyze health wiki-health idea-loop jam prepost carousel sequence-check patterns publication insights results visual-check identity-health article feedback-integrations feedback-integrations-setup publish publish-dry-run test

help:
	@printf "%s\n" "AI command center commands:"
	@printf "%s\n" "  make brief                       Show today's creator/engineering brief"
	@printf "%s\n" "  make analyze                     Compare saved post performance with source evidence"
	@printf "%s\n" "  make health NOTE='...'           Run wiki/memory health with write + index fix"
	@printf "%s\n" "  make idea-loop                   Discover and verify one fresh Instagram idea"
	@printf "%s\n" "  make jam MOMENT='...'            Prepare a carousel jam prompt/command"
	@printf "%s\n" "  make prepost CONCEPT='...'       Run planned Reel pre-post analysis"
	@printf "%s\n" "  make carousel STORY='...'        Create a draft; CREATIVE_BRIEF=path prepares one proof"
	@printf "%s\n" "  make sequence-check CAROUSEL=path Validate story plan, beats and review fingerprint"
	@printf "%s\n" "  make patterns QUERY='...'         Recall two reviewed mechanisms after the first draft"
	@printf "%s\n" "  make publication CAROUSEL=path RECORD=path Link an already published post"
	@printf "%s\n" "  make insights SHORTCODE=... RECORD=path Save one dated native Insights snapshot"
	@printf "%s\n" "  make results SHORTCODE=...        Review linked outcomes and next hypothesis"
	@printf "%s\n" "  make visual-check CAROUSEL=path  Check directed story before/after imagegen"
	@printf "%s\n" "  make identity-health CAROUSEL=path Check identity lock closed-loop propagation"
	@printf "%s\n" "  make article CAROUSEL=path       Create Substack article package"
	@printf "%s\n" "  make feedback-integrations       Report optional SDK and calibration readiness"
	@printf "%s\n" "  make feedback-integrations-setup Install pinned SDKs in an isolated opt-in venv"
	@printf "%s\n" "  make publish NOTE='...'          Run safe verify -> commit -> push gate"
	@printf "%s\n" "  make publish-dry-run NOTE='...'  Preview safe publish scope"
	@printf "%s\n" "  make test                        Run the local test suite"

brief:
	$(PY) scripts/daily_creator_brief.py

analyze:
	$(PY) -m pipeline.stages.a3_analyzer

health wiki-health:
	$(PY) scripts/run_content_health.py --session-note "$(NOTE)"

idea-loop:
	$(PY) scripts/instagram_idea_loop.py run $(if $(DRY_RUN),--dry-run)

jam:
	$(PY) scripts/jam_today.py $(if $(MOMENT),--moment "$(MOMENT)") $(if $(filter command line environment override,$(origin SLIDES)),--slides "$(SLIDES)")

prepost:
	$(PY) scripts/analyze_prepost.py $(if $(CONCEPT),--concept "$(CONCEPT)") $(if $(HOOK),--hook "$(HOOK)") $(if $(CAPTION),--caption "$(CAPTION)") $(if $(EDIT),--edit "$(EDIT)") $(if $(AUDIO),--audio "$(AUDIO)") $(if $(COVER),--cover "$(COVER)")

carousel:
	$(PY) scripts/carousel.py create $(if $(STORY_FILE),--story-file "$(STORY_FILE)",$(if $(STORY),--story "$(STORY)")) $(if $(TITLE),--title "$(TITLE)") $(if $(filter command line environment override,$(origin SLIDES)),--slide-count "$(SLIDES)") $(if $(CREATIVE_BRIEF),--creative-brief "$(CREATIVE_BRIEF)" --prepare-proof,$(if $(PREPARE_PROOF),--prepare-proof)) $(if $(OUTPUT_ROOT),--output-root "$(OUTPUT_ROOT)") $(if $(PROOF_SLIDE),--proof-slide "$(PROOF_SLIDE)") $(foreach image,$(STORY_IMAGES) $(IMAGE),--story-image "$(image)") $(foreach identity,$(IDENTITY_IMAGES) $(IDENTITY_IMAGE),--identity-image "$(identity)") $(foreach format,$(FORMATS),--format "$(format)")

sequence-check:
	@test -n "$(CAROUSEL)" || (printf "%s\n" "Usage: make sequence-check CAROUSEL=output/carousels/YYYY-MM-DD/slug"; exit 2)
	$(PY) scripts/carousel.py sequence-check "$(CAROUSEL)"

patterns:
	@test -n "$(QUERY)" || (printf "%s\n" "Usage: make patterns QUERY='specific couple mechanism'"; exit 2)
	$(PY) scripts/carousel.py patterns --query "$(QUERY)"

publication:
	@test -n "$(CAROUSEL)" -a -n "$(RECORD)" || (printf "%s\n" "Usage: make publication CAROUSEL=path RECORD=publication.json"; exit 2)
	$(PY) scripts/carousel.py publication "$(CAROUSEL)" --record "$(RECORD)"

insights:
	@test -n "$(SHORTCODE)" -a -n "$(RECORD)" || (printf "%s\n" "Usage: make insights SHORTCODE=CODE RECORD=insights.json"; exit 2)
	$(PY) scripts/carousel.py insights "$(SHORTCODE)" --record "$(RECORD)"

results:
	@test -n "$(SHORTCODE)" || (printf "%s\n" "Usage: make results SHORTCODE=CODE"; exit 2)
	$(PY) scripts/carousel.py results "$(SHORTCODE)"

visual-check:
	@test -n "$(CAROUSEL)" || (printf "%s\n" "Usage: make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=pre|post|all"; exit 2)
	$(PY) .agents/skills/a-story-direct-visual-story/scripts/check_visual_story.py --carousel-dir "$(CAROUSEL)" --phase "$(PHASE)"

article:
	@test -n "$(CAROUSEL)" || (printf "%s\n" "Usage: make article CAROUSEL=output/carousels/YYYY-MM-DD/slug TITLE='Optional title'"; exit 2)
identity-health:
	@test -n "$(CAROUSEL)" || (printf "%s\n" "Usage: make identity-health CAROUSEL=output/carousels/YYYY-MM-DD/slug"; exit 2)
	$(PY) pipeline/stages/health_checks.py --carousel "$(CAROUSEL)"

feedback-integrations:
	$(FEEDBACK_INTEGRATIONS_PY) evals/runner.py calibration-status

feedback-integrations-setup:
	$(PY) -m venv "$(FEEDBACK_INTEGRATIONS_VENV)"
	$(FEEDBACK_INTEGRATIONS_VENV)/bin/python -m pip install 'deepeval==4.2.1' 'langfuse==4.15.1'
	$(FEEDBACK_INTEGRATIONS_VENV)/bin/python evals/runner.py calibration-status

publish:
	$(PY) scripts/autopublish.py --session-note "$(NOTE)" $(foreach include,$(INCLUDE),--include "$(include)") $(if $(NO_PUSH),--no-push)

publish-dry-run:
	$(PY) scripts/autopublish.py --dry-run --session-note "$(NOTE)" $(foreach include,$(INCLUDE),--include "$(include)") $(if $(NO_PUSH),--no-push)

test:
	$(PY) -m pytest --import-mode=importlib tests
