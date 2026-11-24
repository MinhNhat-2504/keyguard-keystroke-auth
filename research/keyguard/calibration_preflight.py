"""Research preflight for the existing 20-sample, five-fold calibration.

Warnings constrain the behavioral path; they do not authenticate a user,
prove security, change scores, or certify profiles without warnings.
"""
from dataclasses import asdict, dataclass
import math
import numpy as np

from keyguard.detectors import ScaledManhattan

MAD_FLOOR = 1e-9
CV_STD_FLOOR = 1e-6

@dataclass(frozen=True)
class FoldFloorEvent:
    fold: int
    feature_index: int
    held_rows_1based: tuple[int, ...]
    maximum_held_deviation: float
    maximum_contribution: float

@dataclass(frozen=True)
class CalibrationAudit:
    feature_count: int
    cv_center: float
    cv_std_unfloored: float
    cv_scale: float
    oof_scores: tuple[float, ...]
    floor_extrapolations: tuple[FoldFloorEvent, ...]
    cv_std_at_floor: bool

    @property
    def review_required(self) -> bool:
        return bool(self.floor_extrapolations) or self.cv_std_at_floor

    def to_dict(self) -> dict:
        result = asdict(self)
        result['review_required'] = self.review_required
        return result

def audit_calibration(enrollment) -> CalibrationAudit:
    """Uses enrollment only; exactly the original contiguous five-fold split."""
    try:
        x = np.asarray(enrollment, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError('Twenty finite feature vectors required') from exc
    if x.ndim != 2 or x.shape[0] != 20 or x.shape[1] == 0 or not np.isfinite(x).all():
        raise ValueError('Twenty finite feature vectors required')
    events = []
    scores = np.empty(20, dtype=float)
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            for fold, held in enumerate(np.array_split(np.arange(20), 5), 1):
                model = ScaledManhattan().fit(np.delete(x, held, axis=0))
                deviations = np.abs(x[held] - model.mean_)
                scores[held] = model.score(x[held])
                for j in np.flatnonzero(model.mad_ <= MAD_FLOOR):
                    delta = float(deviations[:, j].max())
                    if delta > MAD_FLOOR:
                        events.append(FoldFloorEvent(fold, int(j), tuple(int(k)+1 for k in held),
                                                     delta, delta / float(model.mad_[j])))
            center = float(scores.mean())
            std = float(scores.std())
    except FloatingPointError as exc:
        raise ValueError('Calibration arithmetic must remain finite') from exc
    if not np.isfinite(scores).all() or not math.isfinite(center) or not math.isfinite(std):
        raise ValueError('Calibration arithmetic must remain finite')
    return CalibrationAudit(x.shape[1], center, std, max(std, CV_STD_FLOOR),
                            tuple(float(v) for v in scores), tuple(events), std <= CV_STD_FLOOR)

def behavioral_acceptance_allowed(audit: CalibrationAudit, z: float, threshold: float) -> bool:
    """Prototype gate; caller must use the audit for the same enrollment profile.

    False means additional verification is required, never successful login.
    This function has no OTP outcome or production authentication side effects.
    """
    if not isinstance(audit, CalibrationAudit):
        raise ValueError('CalibrationAudit required')
    if not math.isfinite(z) or not math.isfinite(threshold):
        raise ValueError('Finite score and threshold required')
    return not audit.review_required and z <= threshold
