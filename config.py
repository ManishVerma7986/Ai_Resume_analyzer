import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
SAMPLES_DIR = os.path.join(BASE_DIR, "sample_resumes")

# Scoring weights (can be tweaked)
TFIDF_WEIGHT = 0.7
SKILL_WEIGHT = 0.3

# Limits
MAX_UPLOAD_SIZE_MB = 5
