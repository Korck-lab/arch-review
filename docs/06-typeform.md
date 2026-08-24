# Bounty typeform (https://form.typeform.com/to/jLfT7v7o)

Real fields (read 20/Aug/2026):
1. **Your E-Mail**
2. **Experience examples** (open-access bounties / environments on the Hub / LLM projects)
3. **Which Application-Only bounties do you want**
4. **Profiles/Links**
5. **Free field**

**Process rule (agreed): the final submission is Rafael's decision and Rafael's click.**
The answers below are prepared for his review. Nothing is submitted without an explicit ok.

---

## Prepared answers

### 1. Your E-Mail
```
rafael.aguilher@gmail.com
```

### 2. Experience examples
```
arch-review is an eval environment for architectural code review, published on the
Environments Hub. Repo: https://github.com/Korck-lab/arch-review
Hub: <FILL AFTER `prime env push`>

A reviewer model reads a diff carrying seeded, documented defects and writes a free-form
code review. Scoring is a two-stage, gold-blind judge pipeline: a claim extractor turns the
review into one claim per distinct issue, then a matcher maps each claim to the seeded gold
as a defect, a planted distractor or a false alarm. The reward is the F1 of defect recall
against claim precision. A model cannot win by listing everything, because every false
alarm costs precision. It cannot win by staying silent either: an empty review scores
recall 0.

I wrote the seven-category defect taxonomy and every gold justification by hand, out of
thirty years of engineering and CTO due-diligence work. The design decisions are recorded
as 29 ADRs in the repo, including the one that forces hard tasks to decompose into
single-defect sub-tasks so a score is attributable to a mechanism rather than to a bundle.
```

### 3. Which Application-Only bounties do you want
```
SWE-Swiss (Full Pipeline)
```
Plan B, same credential: BFCL-v4, AppWorld, Xbench-DeepSearch.

### 4. Profiles/Links
```
GitHub:   https://github.com/Korck-lab
LinkedIn: https://linkedin.com/in/rafael-costa-tech
```

### 5. Free field
```
I have thirty years in software engineering, most recently as a CTO, and the part of the
job I did most often was reading a diff and deciding what would break in production. That
is the judgment arch-review tries to measure, and building it is what convinced me the
harder half of this work is the eval, not the model.

SWE-Swiss appeals to me for the same reason. Its three skills are localization, repair and
unit-test generation, which is the decomposition I would have chosen myself, and
reproducing a published score on the full suite is a verification problem before it is a
training one. I would rather be judged on a faithful reproduction than on a clever variation.
```

---

## Pre-submission checklist
- [ ] `prime env push` done; paste the Hub URL into answer 2
- [ ] Repo public and readable at the URL in answer 4
- [ ] README results table matches the published environment
- [ ] Rafael reads all five answers
- [ ] Rafael submits
