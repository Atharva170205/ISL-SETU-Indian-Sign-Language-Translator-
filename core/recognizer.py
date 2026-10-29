"""
core/recognizer.py — Loads the trained model and provides word prediction.
"""

import os
import numpy as np
import torch

from core.preprocess import sequence_to_features
from core.model import SignClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "production.pt")
CONFIDENCE_THRESHOLD = 0.60  # Below this, return unclear=True


class SignRecognizer:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = MODEL_PATH

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)

        self.vocab = list(checkpoint["vocab"])
        config = checkpoint.get("config", {})

        self.model = SignClassifier(
            input_dim=config.get("input_dim", 126),
            hidden_dim=config.get("hidden_dim", 128),
            num_layers=config.get("num_layers", 2),
            num_classes=len(self.vocab),
            dropout=config.get("dropout", 0.3),
        )
        self.model.load_state_dict(checkpoint["model_state"])
        self.model.to(self.device)
        self.model.eval()

    def predict(self, raw_frames: np.ndarray, top_k: int = 3):
        """
        raw_frames: list or array of (2, 21, 3) landmark frames
        Returns: {"word": str|None, "confidence": float, "alternatives": [...], "unclear": bool}
        """
        if len(raw_frames) == 0:
            return {"word": None, "confidence": 0.0, "alternatives": [], "unclear": True}

        features = sequence_to_features(np.array(raw_frames))  # (T, 126)
        features = torch.FloatTensor(features).unsqueeze(0).to(self.device)  # (1, T, 126)
        lengths = torch.LongTensor([features.shape[1]]).to(self.device)

        with torch.no_grad():
            logits = self.model(features, lengths)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        order = np.argsort(probs)[::-1][:top_k]
        top_prob = float(probs[order[0]])
        alternatives = [
            {"word": self.vocab[i], "confidence": float(probs[i])} for i in order
        ]

        if top_prob < CONFIDENCE_THRESHOLD:
            return {
                "word": None,
                "confidence": top_prob,
                "alternatives": alternatives,
                "unclear": True,
            }

        return {
            "word": alternatives[0]["word"],
            "confidence": top_prob,
            "alternatives": alternatives,
        }