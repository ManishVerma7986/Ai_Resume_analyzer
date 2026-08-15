import os
import csv
from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import namedtuple
from config import DATA_DIR, TFIDF_WEIGHT, SKILL_WEIGHT


JobRole = namedtuple('JobRole', ['role', 'description', 'required_skills'])


def load_job_roles(path: str) -> List[JobRole]:
    roles = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"Job roles file not found: {path}")
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            skills = [s.strip() for s in row.get('required_skills', '').split(';') if s.strip()]
            roles.append(JobRole(role=row.get('role','').strip(), description=row.get('description','').strip(), required_skills=skills))
    return roles


def compute_similarity_scores(resume_text: str, job_roles: List[JobRole], tfidf_weight=TFIDF_WEIGHT, skill_weight=SKILL_WEIGHT, detected_skills: List[str]=None) -> List[dict]:
    """Return list of dicts with role, tfidf_score, skill_coverage, final_score"""
    corpus = [resume_text] + [jr.description + ' ' + ' '.join(jr.required_skills) for jr in job_roles]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf = vectorizer.fit_transform(corpus)

    resume_vec = tfidf[0]
    role_vecs = tfidf[1:]

    sims = cosine_similarity(resume_vec, role_vecs).flatten()

    results = []
    detected_set = set([s.lower() for s in (detected_skills or [])])

    for i, jr in enumerate(job_roles):
        tfidf_score = float(sims[i]) if not np.isnan(sims[i]) else 0.0

        # skill coverage
        if jr.required_skills:
            matched = 0
            for rs in jr.required_skills:
                if rs.lower() in detected_set:
                    matched += 1
            coverage = matched / len(jr.required_skills)
        else:
            coverage = 0.0

        final_score = tfidf_weight * tfidf_score + skill_weight * coverage

        results.append({
            'role': jr.role,
            'tfidf_score': round(tfidf_score * 100, 2),
            'skill_coverage': round(coverage * 100, 2),
            'final_score': round(final_score * 100, 2),
            'required_skills': jr.required_skills,
        })

    # sort by final_score desc
    results = sorted(results, key=lambda x: x['final_score'], reverse=True)
    return results
