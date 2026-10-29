# EduSense AI — User Acceptance Testing (UAT) & Edge Case Checklist

**Date:** 29 October 2026  
**Target Environment:** Windows 10/11, Ubuntu 20.04+, macOS  
**Specification Ref:** SRS Epic 6 (FR-6.4) & Acceptance Criteria  

---

## 1. Acceptance Criteria Verification

| Test ID | Test Scenario | Acceptance Criteria | Verified Result | Status |
|:---:|:---|:---|:---|:---:|
| **UAT-AC-1** | Presence Duration Threshold | Attendance is marked `Present` only when cumulative presence $\ge$ threshold (60s default). | `test_acceptance_criteria_1_presence_duration` passed in test runner. | **PASSED** |
| **UAT-AC-2** | Multimodal Fusion Timeline | Engagement timeline renders with both vision (attention/movement) and audio (dB/VAD) contributing. | `test_acceptance_criteria_2_multimodal_timeline` verified formula weights. | **PASSED** |
| **UAT-AC-3** | Teaching Suggestion Variety | At least 3 distinct suggestion types (`alert`, `warning`, `info`) generated from classroom patterns. | `test_acceptance_criteria_3_recommendation_types` verified rule triggers. | **PASSED** |
| **UAT-AC-4** | Non-Punitive Ethics | Student session summaries contain **zero grades, marks, or peer ranking**, providing reflective notes only. | `test_acceptance_criteria_4_student_summary_no_grades` verified clean payloads. | **PASSED** |
| **UAT-AC-5** | Export Generation | PDF and CSV export endpoints return valid downloadable documents with attendance & metrics. | `test_acceptance_criteria_5_exports` verified CSV headers and `%PDF` binary header. | **PASSED** |

---

## 2. Edge Case Validation Matrix (FR-6.4)

### Edge Case 1: Low-Light Illumination
- **Condition:** Classroom lights dimmed for projector slide presentation (mean pixel luminance < 60).
- **Mitigation:** `CameraService.preprocess_frame` checks mean luminance and applies gamma enhancement ($1.0 / 1.5$) with histogram equalization to recover facial contrast for Haar Cascade.
- **Verification:** Verified faces continue to be detected when brightness drops.

### Edge Case 2: Background Noise & Side Chatter
- **Condition:** Rustling papers, air conditioning hum, or side murmur (noise between -35 dB and -18 dB without clear voiced formants).
- **Mitigation:** `AudioAnalyzer.analyze_window` computes Zero-Crossing Rate (ZCR) and subframe energy ratio to classify noise as `background noise` rather than `active speech`. Triggers `RULE_NOISY_INTERVAL` warning without penalizing individual student records.
- **Verification:** Verified room acoustic state accurately flags `background noise`.

### Edge Case 3: Partial Occlusion & Head Movement
- **Condition:** Student looks down to write notes, turns sideways, or rests chin on hand for 1–2 seconds.
- **Mitigation:** `MultiObjectTracker` maintains track state for up to `max_age` (30–35 frames) without terminating the ID. Kalman / centroid prediction bridges the occlusion gap.
- **Verification:** ID remains persistent (`Student_01`) when the face re-appears.

### Edge Case 4: Short / Fleeting Appearances
- **Condition:** Someone walks past the doorway or enters the camera view for 4 seconds to drop off notes.
- **Mitigation:** Cumulative presence accumulator leaves status as `Absent` ($< 10$s) or `Partial`, preventing false positive full attendance marks.
- **Verification:** Only attendees accumulating $\ge$ 60 seconds are marked `Present`.

### Edge Case 5: Missing or Intermittent Microphone Audio
- **Condition:** Browser blocks microphone permission or microphone disconnects mid-lecture.
- **Mitigation:** System degrades gracefully (`NFR-4`). Engagement engine falls back to visual-attention and movement scoring with baseline neutral acoustic weighting; UI surfaces clear advisory indicator without crashing.
- **Verification:** Verified live stream continues functioning with audio in standby mode.
