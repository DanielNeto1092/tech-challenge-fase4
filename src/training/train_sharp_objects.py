"""Train YOLOv8 on Sharp Objects Detection dataset with automatic val split."""
from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path


def _auto_split_train(data_dir: Path, val_ratio: float = 0.2, seed: int = 42) -> None:
    """Se val/ não existir, separa val_ratio% do train/ automaticamente."""
    train_images = data_dir / "train" / "images"
    train_labels = data_dir / "train" / "labels"
    val_images = data_dir / "valid" / "images"
    val_labels = data_dir / "valid" / "labels"

    if val_images.exists() and any(val_images.iterdir()):
        return  # val já existe

    if not train_images.exists():
        raise FileNotFoundError(f"Train images not found: {train_images}")

    all_images = sorted(train_images.glob("*.*"))
    random.seed(seed)
    random.shuffle(all_images)
    split_idx = int(len(all_images) * (1 - val_ratio))
    val_set = all_images[split_idx:]

    val_images.mkdir(parents=True, exist_ok=True)
    val_labels.mkdir(parents=True, exist_ok=True)

    for img in val_set:
        label = train_labels / f"{img.stem}.txt"
        shutil.move(str(img), str(val_images / img.name))
        if label.exists():
            shutil.move(str(label), str(val_labels / label.name))

    print(f"Auto-split: moved {len(val_set)} images to valid/ ({val_ratio*100:.0f}% of train)")


def _build_data_yaml(data_dir: Path) -> Path:
    """Gera data.yaml com caminhos absolutos para o Ultralytics."""
    import yaml

    original = data_dir / "data.yaml"
    if not original.exists():
        raise FileNotFoundError(f"data.yaml not found: {original}")

    cfg = yaml.safe_load(original.read_text(encoding="utf-8")) or {}

    train_path = data_dir / "train" / "images"
    val_path = data_dir / "valid" / "images"
    test_path = data_dir / "test" / "images"

    resolved = {
        "train": str(train_path),
        "val": str(val_path) if val_path.exists() else str(train_path),
        "test": str(test_path) if test_path.exists() else str(val_path if val_path.exists() else train_path),
        "nc": int(cfg.get("nc", 0)),
        "names": list(cfg.get("names", [])),
    }

    out = data_dir / "data_resolved.yaml"
    out.write_text(yaml.safe_dump(resolved, sort_keys=False), encoding="utf-8")
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train YOLOv8 Sharp Object Detector")
    p.add_argument("--data-dir", default="Sharp Objects Detection.yolov8", help="Dataset root")
    p.add_argument("--model", default="yolov8n.pt", help="Base model")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--name", default="sharp_object_detector")
    p.add_argument("--project", default="runs/detect")
    p.add_argument("--device", default=None)
    p.add_argument("--val-ratio", type=float, default=0.2, help="Val split ratio if val/ missing")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = Path(args.data_dir)

    if not data_dir.exists():
        raise SystemExit(f"ERROR: dataset not found: {data_dir}")

    # Step 1: auto-split se necessário
    _auto_split_train(data_dir, val_ratio=args.val_ratio, seed=args.seed)

    # Step 2: gerar yaml com caminhos absolutos
    data_yaml = _build_data_yaml(data_dir)

    # Step 3: treinar
    from ultralytics import YOLO
    model = YOLO(args.model)

    kwargs: dict = {
        "data": str(data_yaml),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "name": args.name,
        "project": args.project,
    }
    if args.device:
        kwargs["device"] = args.device

    model.train(**kwargs)
    print(f"Training complete. Weights: {args.project}/{args.name}/weights/best.pt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
