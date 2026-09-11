"""Fine-tune a MobileNetV3 binary classifier (obstacle vs. clear path) on
frames collected by data_collector_node.py.

This replaces the ImageNet-pretrained placeholder used in
explainable_nav/gradcam.py with a model that actually understands the
obstacle-detection task, so both the confidence scores and the Grad-CAM
heatmaps become meaningful for this specific robot/environment.

Usage:
    python train_classifier.py --data-dir ../training/data --epochs 10
"""

import argparse
import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models, transforms


def build_model(num_classes: int = 2) -> nn.Module:
    model = models.mobilenet_v3_small(weights="IMAGENET1K_V1")
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def get_dataloaders(data_dir: str, batch_size: int, val_split: float = 0.2):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                              std=[0.229, 0.224, 0.225]),
    ])

    full_dataset = datasets.ImageFolder(data_dir, transform=transform)
    val_size = int(len(full_dataset) * val_split)
    train_size = len(full_dataset) - val_size
    train_ds, val_ds = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader, full_dataset.classes


def train(data_dir: str, epochs: int, batch_size: int, lr: float, out_path: str):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_loader, val_loader, classes = get_dataloaders(data_dir, batch_size)
    print(f"Classes (index order matters for inference): {classes}")

    model = build_model(num_classes=len(classes)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)

        train_loss = running_loss / len(train_loader.dataset)

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        val_acc = correct / total if total > 0 else 0.0
        print(f"Epoch {epoch + 1}/{epochs} | train_loss={train_loss:.4f} | val_acc={val_acc:.4f}")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "classes": classes}, out_path)
    print(f"Saved fine-tuned model to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="./data",
                         help="Directory with obstacle/ and clear/ subfolders")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--out", default="./checkpoints/obstacle_classifier.pt")
    args = parser.parse_args()

    train(args.data_dir, args.epochs, args.batch_size, args.lr, args.out)
