"""core/model.py — BiLSTM sign classifier over landmark sequences."""
import torch
import torch.nn as nn


class SignClassifier(nn.Module):
    """Bidirectional LSTM over per-frame landmark features.

    Input:  (batch, T, 126)   126 = 2 hands x 21 landmarks x (x, y, z)
    Output: (batch, num_classes) logits
    """

    def __init__(self, input_dim=126, hidden_dim=128, num_layers=2,
                 num_classes=32, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_dim, hidden_dim, num_layers,
            batch_first=True, bidirectional=True, dropout=dropout,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x, lengths):
        # pack so padded frames don't contaminate the LSTM state
        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths.cpu(), batch_first=True, enforce_sorted=False)
        out, _ = self.lstm(packed)
        out, _ = nn.utils.rnn.pad_packed_sequence(out, batch_first=True)
        # mean-pool over valid (non-padded) frames only
        mask = (torch.arange(out.size(1), device=x.device).unsqueeze(0)
                < lengths.unsqueeze(1).to(x.device))
        pooled = (out * mask.unsqueeze(-1)).sum(1) / lengths.unsqueeze(1).clamp(min=1)
        return self.fc(self.dropout(pooled))