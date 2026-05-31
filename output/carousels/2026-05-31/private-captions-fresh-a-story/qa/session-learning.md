# Session Learning

date: 2026-05-31
status: BLOCKED_UNTIL_CORRECTED_IDENTITY_HEIGHT_PROOF

The Private Captions fresh carousel must not continue as a full batch until
one corrected proof passes identity and height QA.

Creator correction:

- Himanshu/Zuv is 5'8".
- Aanchal/Aachu is 5'6".
- The visible difference is only two inches.
- Faces must match the supplied identity references, not generic South Asian
  illustration faces.
- Aanchal must not be scaled down; Himanshu must not be made oversized, lanky,
  or chiseled.

Generation rule:

Use the supplied reference screenshots for paired-label grammar, blocking, and
exact text only. Use actual Aachu/Zuv identity images as face and scale inputs.
If the image-generation path ignores references or produces an unrelated
artifact, stop and switch paths instead of calling the output usable.
