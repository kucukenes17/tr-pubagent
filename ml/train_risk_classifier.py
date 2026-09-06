"""XLM-R tabanlı çok sınıflı eylem risk sınıflandırıcısını eğitir."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from datasets import Dataset, DatasetDict
from sklearn.metrics import classification_report, f1_score
from transformers import (
    AutoModelForSequenceClassification, AutoTokenizer,
    DataCollatorWithPadding, EarlyStoppingCallback, Trainer, TrainingArguments,
)


MODEL_ID = "FacebookAI/xlm-roberta-base"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml_guard import classifier_feature_text


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("outputs/risk_dataset.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("outputs/xlmr-risk"))
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()

    rows = load_rows(args.data)
    labels = sorted({row["label"] for row in rows})
    label2id = {label: index for index, label in enumerate(labels)}
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    def to_dataset(split: str) -> Dataset:
        selected = [row for row in rows if row["split"] == split]
        dataset = Dataset.from_list(selected)
        return dataset.map(
            lambda batch: tokenizer(
                [classifier_feature_text(request, state, action) for request, state, action in zip(
                    batch["user_request"],
                    batch.get("current_state_structured", batch["current_state"]),
                    batch.get("proposed_action_structured", batch["proposed_action"]),
                )],
                truncation=True, max_length=256,
            ) | {"labels": [label2id[label] for label in batch["label"]]},
            batched=True,
            remove_columns=dataset.column_names,
        )

    dataset = DatasetDict({split: to_dataset(split) for split in ("train", "validation", "test")})
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, num_labels=len(labels), id2label={value: key for key, value in label2id.items()}, label2id=label2id)

    def metrics(prediction):
        predictions = np.argmax(prediction.predictions, axis=1)
        return {"macro_f1": f1_score(prediction.label_ids, predictions, average="macro")}

    training = TrainingArguments(
        output_dir=str(args.output), learning_rate=2e-5,
        per_device_train_batch_size=16, per_device_eval_batch_size=32,
        num_train_epochs=args.epochs, weight_decay=0.01,
        eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
        metric_for_best_model="macro_f1", greater_is_better=True,
        save_only_model=True, save_total_limit=1,
        report_to="none", seed=42, fp16=True,
    )
    trainer = Trainer(model=model, args=training, train_dataset=dataset["train"], eval_dataset=dataset["validation"], processing_class=tokenizer, data_collator=DataCollatorWithPadding(tokenizer), compute_metrics=metrics, callbacks=[EarlyStoppingCallback(early_stopping_patience=2)])
    trainer.train()
    test_result = trainer.predict(dataset["test"])
    predicted = np.argmax(test_result.predictions, axis=1)
    report = classification_report(test_result.label_ids, predicted, target_names=labels, output_dict=True)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "test_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    metadata = {
        "feature_schema": rows[0].get("feature_schema", "xlmr-risk-v1-text"),
        "base_model": MODEL_ID,
        "labels": labels,
        "rows": len(rows),
        "data_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "recommended_runtime_threshold": 0.80,
    }
    (args.output / "training_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)
    print(json.dumps({"macro_f1": report["macro avg"]["f1-score"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
