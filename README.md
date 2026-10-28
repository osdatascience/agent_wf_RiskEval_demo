# agent_wf_RiskEval_demo

AI assistant support answers are evaluated in 4 tests.
An overall score of 96% and a 95% threshold say "ready to deploy" 
The other three reports on the same data say you can't.

## Quick start

Only `python` required, without any additional packages. No live model or API keys are needed: the answers are already recorded in  `data/`.

```bash
git clone https://github.com/osdatascience/agent_wf_RiskEval_demo.git
cd agent_wf_RiskEval_demo
./run.sh
```

`run.sh` regenerates the data with the generator, verifies that it matches `data/` byte-by-byte, prints the reports, 
and compares the output against `expected.txt`.

CI gate with exit code 1 on violation of a hard invariant:

```bash
python eval.py --strict
```

## Output

**1. Overall score and categories.** 1018 correct runs out of 1060, (96.0%)

| Category |	Accuracy |	Runs |
|---|---:|---:|
| typical questions ('typical') | 99,5% | 600 |
| refunds and money (refunds) | 98,0% | 200 |
| personal data ('personal_data') | 100,0% | 100 |
| out-of-scope questions ('out_of_scope') | 73,3% | 60 |
| rare phrasings ('rare_wording') | 81,0% | 100 |

Typical questions make up the largest share and pull the average score up. Out-of-scope questions and rare phrasings account for 35 of the 42 incorrect runs, but this is not visible in the overall score.

**2. Gate.** The accuracy of 96.0% passes the 95% threshold. However, in two runs, the assistant promised a refund beyond policy (promise_beyond_policy). This is a hard invariant: there must be zero observed violations in the test set, so the gate result is FAIL. Zero observed violations do not prove that they will not occur in production: hard invariants are additionally sustained by checks within the application itself, not just by evals. In another run of the same case, the answer was correct: a single test would have easily missed this error.

**3. LLM-as-a-judge.** On 200 labeled answers with 26 violations:

| Metrics | Value |
|---|---:|
| matches with human | 97,0% |
| precision | 95,5% |
| recall | 80,8% (5 out of 26 were missed) |
| recall, 95% Wilson interval | 62,1–91,5% |
| judge "always no", for comparison | match 87,0%, recall 0% |

The high match rate masks the fact that on this sample, the judge missed almost every fifth violation. Even a judge who checks nothing at all would agree with humans in 87% of cases. The interval also shows the converse: 26 violations are too few for a confident conclusion about the judge in general, and the sample needs to be expanded.

**4. Working set vs holdout set.** After prompt adjustments made with the working set in mind, it scores 98% on it. On the holdout set, which was not used during tuning, it is 85%. A 13-point difference is overfitting, not quality.

## Scope of Applicability

The data is synthetic. The composition is explicitly defined in generate_data.py. This is an illustration of the measurement mechanics, not an evaluation of a specific model.

Manual labeling and judge verdicts are recorded as pre-existing fields. 

The 95% threshold and zero-tolerance policy for invariants are examples. Real-world thresholds are set by the Use case owner.

## Structure

| File | Description |
|---|---|
| `data/runs.jsonl` | regression set: 106 cases with 10 runs each, category, response, manual label, type of violation |
| `data/judge_sample.jsonl` | 200 answers with labels and LLM-as-a-judge output |
| `data/tuning.jsonl` | working set and holdout set with 100 answers each |
| `generate_data.py` | data generator with a fixed seed |
| `eval.py` | four reports and gate `--strict` |
| `expected.txt` | reference output of `eval.py` |
| `run.sh` | verification of data and output reproducibility |
| `.github/workflows/check.yml` | same in CI, plus a check that the gate fails |

