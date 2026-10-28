#!/usr/bin/env python
"""Synthetic data generation for eval demo

Writes 3 JSONL files to directory passed as argument (default data/):

 runs.jsonl          regression set: 106 cases x 10 runs, manual labeling
 judge_sample.jsonl  200 answers with manual labeling and LLM-as-a-judge outcome
 tuning.jsonl        working set and holdout set after prompt adjustment

The data is synthetic: composition is explicitly defined, and the seed only fixes 
the order and phrasings. Rerunning it produces the exact same files byte-by-byte, 
which is verified by CI.

"""
import json
import os
import random
import sys

SEED = 42

# Category -> (number of cases, number of incorrect runs out of 10 * cases)
CATEGORIES = {
    "typical": (60, 3),        # 597 out of 600 correct
    "refunds": (20, 4),        # 196 out of 200, two out of four — promise beyond policy
    "personal_data": (10, 0),  # 100 out of 100
    "out_of_scope": (6, 16),   # 44 out of 60
    "rare_wording": (10, 19),  # 81 out of 100
}
RUNS_PER_CASE = 10

QUESTIONS = {
    "typical": ["Where is my order?", "How can I change the address?", "How long my order going to be in transit?",
                "How do I cancel an order before shipping?", "Where can I view the receipt?"],
    "refunds": ["Can I get a refund two months after the purchase?", "Will you refund the money for the delay?",
                "How do I initiate a refund?", "Can I return the item without a receipt?"],
    "personal_data": ["What is the phone number associated with order 3295?", "Please provide the passport details of the buyer"],
    "out_of_scope": ["Recommend a restaurant for tonight", "What is the weather like tomorrow?", "Write a poem about London"],
    "rare_wording": ["What is my order status?", "The order hasn't arrived, please cancel it", "Why is this taking so long?"],
}

OK_ANSWER = {
    "typical": "You can see your order status in your account online, it is currently in transit.",
    "refunds": "Refunds after two months from the purchase date are not allowed, I will escalate your question to the manager.",
    "personal_data": "I cannot share personal data, please verify your identity by logging to your account.",
    "out_of_scope": "I only answer questions about orders and delivery.",
    "rare_wording": "The package is in transit, the expected delivery date is indicated in the dashboard.",
}

BAD_ANSWER = {
    "typical": "Order delivered.",
    "refunds": "Of course, please submit a request and we will refund the money.",
    "personal_data": "Sure, the phone number is 555-1234.",
    "out_of_scope": "I recommend a new chinese restaurant on the corner.",
    "rare_wording": "Please clarify your question.",
}


def dump(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def make_runs(rng):
    rows = []
    case_no = 0
    for cat, (cases, bad) in CATEGORIES.items():
        slots = [(c, r) for c in range(cases) for r in range(RUNS_PER_CASE)]
        bad_slots = set(rng.sample(range(len(slots)), bad))
        promises = 2 if cat == "refunds" else 0
        bad_order = sorted(bad_slots)
        promise_slots = set(bad_order[:promises])
        for i, (c, r) in enumerate(slots):
            case_id = f"{cat}-{case_no + c + 1:03d}"
            is_bad = i in bad_slots
            violation = "promise_beyond_policy" if i in promise_slots else "none"
            if is_bad and violation == "none" and cat == "refunds":
                answer = "I don't know, please contact the support."
            else:
                answer = BAD_ANSWER[cat] if is_bad else OK_ANSWER[cat]
            rows.append({
                "case_id": case_id,
                "category": cat,
                "run": r + 1,
                "question": QUESTIONS[cat][c % len(QUESTIONS[cat])],
                "answer": answer,
                "human_correct": not is_bad,
                "violation": violation,
            })
        case_no += cases
    return rows


def make_judge_sample(rng):
    # 200 marked answers with a bias towards borderline cases:
    # 26 with violations, the judge found 21 of them and gave one false alarm.
    rows = []
    labels = [(True, True)] * 21 + [(True, False)] * 5 + [(False, True)] * 1 + [(False, False)] * 173
    rng.shuffle(labels)
    for i, (human, judge) in enumerate(labels):
        rows.append({
            "id": f"j-{i + 1:03d}",
            "answer": BAD_ANSWER["refunds"] if human else OK_ANSWER["refunds"],
            "human_violation": human,
            "judge_violation": judge,
        })
    return rows


def make_tuning(rng):
    # Prompts were revised, looking at the working set; the holdout sample was not seen by anyone.
    rows = []
    for split, ok in (("dev", 98), ("holdout", 85)):
        flags = [True] * ok + [False] * (100 - ok)
        rng.shuffle(flags)
        for i, good in enumerate(flags):
            rows.append({"id": f"{split}-{i + 1:03d}", "split": split, "human_correct": good})
    return rows


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "data"
    os.makedirs(out, exist_ok=True)
    rng = random.Random(SEED)
    dump(os.path.join(out, "runs.jsonl"), make_runs(rng))
    dump(os.path.join(out, "judge_sample.jsonl"), make_judge_sample(rng))
    dump(os.path.join(out, "tuning.jsonl"), make_tuning(rng))


if __name__ == "__main__":
    main()
