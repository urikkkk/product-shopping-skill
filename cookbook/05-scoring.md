# How Scoring Works and How to Customize It

## The four dimensions

Every keyboard is scored on four dimensions, each weighted:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| **Ergonomics** | 40% | Split, tenting, tilt, contoured keywells, thumb clusters, ortholinear |
| **Reviews** | 20% | Rating quality (avg score) + quantity (review count) |
| **Value** | 20% | Price-to-feature ratio (lower price = higher score) |
| **Build** | 20% | Mechanical switches, hot-swap, QMK/VIA, wireless, switch brand |

Each dimension is scored 0-100, then multiplied by its weight.
Maximum possible total: 100.

## Ergonomics scoring (0-100)

| Feature | Points |
|---------|--------|
| Split layout | +30 |
| Tenting | +20 |
| Contoured keywells | +15 |
| Tilt / negative tilt | +10 |
| Wrist rest / palm rest | +10 |
| Thumb clusters | +10 |
| Ortholinear / columnar | +5 |

Capped at 100.

## Reviews scoring (0-100)

```
review_score = (rating / 5.0) * 70 + min(rating_count / 100, 30)
```

- A 5-star rating with 3000+ reviews = 100
- A 0-star rating with no reviews = 0

## Value scoring (0-100)

```
value_score = max(0, 100 - price / 5)
```

- $0 = 100 (free)
- $250 = 50
- $500+ = 0

## Build quality scoring (0-100)

| Feature | Points |
|---------|--------|
| Membrane switch | -30 |
| Hot-swappable | +25 |
| QMK/VIA/ZMK firmware | +30 |
| Bluetooth/2.4GHz wireless | +15 |
| Premium switch brand (Cherry/Kailh/Gateron) | +15 |
| Aluminum build | +15 |

Capped at 0-100.

## How to customize

Edit `src/scoring.py`. The main levers:

### Change weights

```python
W_ERGO = 0.40    # Increase for more ergo-focused ranking
W_REVIEW = 0.20
W_VALUE = 0.20   # Increase for more budget-focused ranking
W_BUILD = 0.20
```

Weights must sum to 1.0.

### Add new ergonomic features

In `score_ergonomics()`, add new keyword checks:

```python
if "adjustable" in features: ergo += 5
if "vertical" in features: ergo += 10
```

### Change the value curve

The current formula is linear. For a logarithmic curve:

```python
import math
value_score = max(0, 100 - math.log(price + 1) * 15)
```

### Disable membrane penalty

Remove the membrane check in `score_build()` to include non-mechanical
keyboards without penalty.
