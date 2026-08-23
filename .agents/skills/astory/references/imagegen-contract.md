# Imagegen Contract

Use built-in Codex `imagegen` only. Do not ask for an OpenAI API key. Do not create a local image provider.

## Required Before Final Generation

1. Run `python3 scripts/prepare_imagegen_reference_context.py --run-id <run_id>` so the run has a machine-readable local reference manifest, raw-identity-first active queue, and supplemental Reference Binder packet images for audit.
2. Make every image in `evals/imagegen_reference_load_plan.json.view_image_queue` visible in the current conversation using `view_image`; this queue must include raw local Aachu and Zuv face-anchor files as first-class active inputs. Binder/contact-sheet images are supplemental review artifacts and must not replace raw face anchors. The creator should not need to attach repo-local identity/style images manually.
   - Current-request screenshots, source illustrations, and inspiration images
     that contain non-Aachu/Zuv faces are analysis-only for final
     identity-sensitive imagegen. Record them in `current_request` and binder
     artifacts, but do not put them in the active `view_image_queue`; describe
     their scene/text/composition lessons in the prompt instead.
3. Confirm each face-visible subject has multiple raw face-anchor view buckets. If four references all teach the same side/profile/front angle or same locked expression, stop and repair the reference set before imagegen.
4. Select style references or load the locked style rules.
5. Confirm exact on-image text.
   - The exact text must be requested inside the imagegen prompt itself.
   - Do not generate blank-text plates for later overlay unless the creator
     explicitly asks for a draft layout proof. A final or creator-review
     candidate with missing on-image text is a hard failure.
6. Confirm native surface: `1080x1350 px` portrait. This phrase must appear in every imagegen prompt.
7. Confirm tiny low-contrast handwritten `@a.storyof.two` top-right brandmark is required in the prompt.
8. Confirm prompt passed pre-generation QA, including `prompt_canvas_size`.
9. Ask for HITL prompt approval.
10. Write `evals/imagegen_reference_visibility_proof.json` before calling `imagegen`. The proof must match the current `load_plan_sha256`, loaded paths, expected count, and raw `aachu_face_identity` / `zuv_face_identity` roles.
11. Run `scripts/astory_repo_qa.py --run-id <run_id> --loop --max-iterations 2` and require `gold_standard_identity_route_gate` to pass before imagegen or final packaging.

If any queued local image cannot be read, if fewer than four raw Aachu face anchors or four raw Zuv face anchors are active, if either person has fewer than two face-anchor view buckets, if `gold_standard_identity_route_gate` fails, or if the active generation path cannot use the loaded image context, mark the run blocked instead of generating final Aachu/Zuv artwork.

Exact-copy source remixes are still illustration runs. A deterministic renderer,
typography layout, quote-card, poster, or decorative background can be used only
as a draft text-placement proof, never as final A Story artwork. Final packaging
requires imagegen illustration proof, passing Image QA, and lived scene evidence;
otherwise block with `QUOTE_CARD_NOT_ILLUSTRATION`.

Exact text is non-negotiable in image generation. Do not call imagegen with
"leave blank space", "add text later", "text overlay later", or equivalent
language for A Story finals or creator-review candidates. The generated artwork
must include the locked on-image text. If imagegen misses, paraphrases,
misspells, omits, or makes the text unreadable, reject immediately with
`TEXT_MISSING_IN_IMAGEGEN` or `TEXT_NOT_EXACT`; do not continue the batch.

Before final imagegen, the Review Room must confirm:
- selected references are local, hashed, and role-separated;
- manual user attachment is not required for existing repo references;
- `gold_standard_identity_route_gate` passes, proving the full route that produced the creator-approved face match: selected references, 4 Aachu face anchors, 4 Zuv face anchors, multi-angle face-anchor diversity, 3 style refs, 11 loaded references, visibility proof, pre-generation eval, agent assignment matrix, prompt-room review, scene landing preview, scene options, selected idea, slide beat map, slide-count decision, required trace states, and prompt language that keeps raw face anchors highest priority while forbidding single-anchor pose/expression copying;
- every face-visible prompt has Aachu and Zuv face identity references;
- every active prompt explicitly asks for native `1080x1350 px` output and contains no square, 1:1, 9:16, or 1080x1080 surface language;
- every active prompt includes the tiny top-right `@a.storyof.two` brandmark;
- every active prompt contains the exact locked on-image text and does not ask
  to leave the text area blank or add text later;
- every active prompt passes `prompt_overload` and `prompt_palette_conflict`;
- every file in `view_image_queue` has been loaded through `view_image` in the current conversation;
- current-request concept images with visible non-Aachu/Zuv people are absent
  from `view_image_queue` and used only through scene notes/prompt text;
- binder-only active queues or binder-only proofs block imagegen with `IDENTITY_REFERENCE_INPUT_UNPROVEN`;
- stale proofs, missing active raw paths, or unexpected loaded paths block imagegen with `REFERENCE_VISIBILITY_PROOF_STALE`, `REFERENCE_VISIBILITY_PROOF_INCOMPLETE`, or `REFERENCE_VISIBILITY_PROOF_PATH_MISMATCH`.
- same-angle/same-expression identity sets block imagegen with `IDENTITY_REFERENCE_DIVERSITY_MISSING`.
- an incomplete gold-standard route blocks imagegen and final package with `GOLD_STANDARD_IDENTITY_ROUTE_MISSING`.

## Generation Rhythm

- Generate one slide at a time.
- If the first candidate for a slide has a hard failure such as `YELLOW_PAPER_CAST`, `IDENTITY_DRIFT`, `STYLE_DRIFT`, `PROMPT_OVERLOAD`, `WRONG_CANVAS_SIZE`, `BRANDMARK_MISSING`, `TEXT_MISSING_IN_IMAGEGEN`, `TEXT_UNREADABLE`, or `TEXT_NOT_EXACT`, stop before generating the next slide and record Image QA.
- Save each candidate in `runs/<run_id>/images/`.
- Save accepted finals in `runs/<run_id>/exports/`.
- Log each generation attempt and decision.

## Retry Rule

Use targeted prompt repair. Do not rewrite the whole prompt randomly.

Retry up to 2 times per failure type. If identity cannot be preserved, mark blocked.
