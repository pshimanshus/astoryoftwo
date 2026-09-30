---
name: non-ai-image-skill
description: Prevent recurring AI-looking defects in locked @a.storyof.two image scenes through risk-specific direction, independent pixel review, and calibrated regression review. Use for visual QA, repair, or a creator complaint about generated-looking art; do not use for open-ended concept work.
---

# Non-AI Image Guard

Use this skill to make an AI-generated image read as a coherent, intentional
@a.storyof.two illustration. It does not determine whether an image was made by
AI, and no automated checker can certify visual correctness or creator taste.

This skill operates after the concept, copy, canvas, and scene facts are locked.
Route open-ended concept work to `$a-story-carousel-jam`; use
`$a-story-direct-visual-story` for the normal package direction and release
path. Canonical rules in `config/rules/` remain authoritative.

## Load only what the task needs

1. Read the current package's correction or exact creator feedback before
   abstracting a lesson. The latest explicit correction supersedes an older one
   only within its stated scope.
2. Read [issue controls](references/issue-controls.md) for the detected risk.
3. Before judging rendered art, read [reviewer procedure](references/reviewer-procedure.md).
4. Read [regression manifest](references/regression-manifest.json) when
   calibrating a reviewer or changing generator, prompts, references, rules, or
   review procedure.

## Route the work by visible risk

Begin with one physical visual sentence: actor, action, target or space, and
visible consequence. Then attach only the checks implied by the scene:

| Scene signal | Required review focus |
| --- | --- |
| Phone, screen, vehicle, tool, parcel, or story-critical prop | object face, orientation, parts, function, owner, and use |
| Touch, handoff, pull, carry, or tight crop | whole owner -> arm -> wrist -> hand -> target chain and contact geometry |
| Door, table, box, wall, seat, floor, threshold, or occlusion | whole silhouettes, support, depth order, and solid-object boundaries |
| Two people, visible face/body/accessory, or a recurring item | identity, adult scale, visible accessory side, wardrobe and state continuity |
| Gaze, gesture, time word, spatial word, or exact copy | silent-read event, eye-line, target, chronology, and copy-to-pixels match |
| Full carousel or explicit style complaint | sequence variety plus house finish, paper, lettering, signature, and canvas |

Do not turn a local correction into a universal ban. In particular, the current
phone correction rejects only a display/UI fused with rear camera lenses on one
phone face. It does **not** impose a new ban on photographic treatment or on
phone UI generally. A visible screen still needs an intended, legible
story-state under the existing text and style rules.

## Direct before generation

Record the minimum scene facts needed to make the review testable: expected
people, camera side, body/prop depth order, object owner and state, hands and
target regions, eye-lines, support planes, time/sequence, locked copy, and
reference attachments. Treat actor anatomical left/right separately from image
left/right. For a sequence, record only facts that must persist or visibly
change between adjacent slides.

Choose the riskiest frame as the proof. A composition that cannot make its
event, contact, object state, or scale readable should be restaged before
generation. More style adjectives are not a repair for a wrong physical
premise.

## Inspect actual pixels and contain failure

Review the decoded current asset for each requested native format. A prompt,
filename, prior QA, generator report, or a checker PASS is not pixel evidence.
Use the procedure's silent read before comparing the intended scene. Bind the
result to the current path, SHA-256, and dimensions through the existing package
workflow; `make visual-check` validates those bindings and authored evidence,
but it does not perform vision.

When a check fails, classify the observable mismatch and repair its cause:

- wrong event, target, chronology, or relationship meaning: restage or replace
  the physical premise;
- wrong owner, object face, hand contact, depth relation, or support: specify
  the missing geometry and regenerate/edit that bounded fault;
- identity, accessory, wardrobe, or state drift: restore the selected reference
  facts and re-inspect the affected sequence;
- finish, extra lettering, exact copy, brandmark, or canvas failure: correct the
  affected final raster and re-inspect it.

Any changed bytes invalidate earlier pixel observations. Keep failed candidates
in quarantine. Do not batch from a failed proof or treat technical PASS as
creator approval. The creator advances the existing proof and final gates.

## Dynamic independent review

When parallel review is authorized, choose only the specialist roles the risk
requires: a blind scene reader for event meaning; a geometry reviewer for
object/contact/topology; a continuity reviewer for adjacent frames; and a
registrar for bindings. Their observations are independent inputs, not new
approval gates. A synthesis reviewer resolves conflicts against current pixels;
an unresolved critical region stays failed or `data_gap`, never PASS.

## Calibration and fresh evidence

The manifest is a finite, labeled calibration set. Use its narrow counterexamples
to avoid teaching the reviewer to reject natural occlusion, permitted poses,
hidden accessories, or every repeated frame. Keep calibration and fresh holdout
cases disjoint by image and repair lineage. After a change, run frozen
calibration first, then use newly collected creator-labeled cases as holdout.
Once a holdout teaches a repair, move it into a later calibration version and
collect a different holdout. Report missing fixtures, false passes, false
rejections, coverage, and unresolved observations; never call a zero-miss sample
a guarantee.
