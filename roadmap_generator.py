from typing import List, Dict


DEFAULT_TEMPLATES = {
    'FastAPI': 'Week 1: FastAPI fundamentals and building simple APIs.',
    'Docker': 'Week 2: Docker basics, containerizing an app, Dockerfiles.',
    'MLflow': 'Week 3: MLflow for experiment tracking and model registry.',
    'Cloud Deployment': 'Week 4: Deploy models to cloud (Heroku/AWS/GCP).',
    'APIs': 'Week 1: Learn building and consuming REST APIs.',
}


def generate_roadmap(missing_skills: List[str]) -> List[str]:
    roadmap = []
    week = 1
    for skill in missing_skills:
        note = DEFAULT_TEMPLATES.get(skill, f'Week {week}: Learn {skill} basics and build a mini-project.')
        roadmap.append(note)
        week += 1
    if not roadmap:
        roadmap = ['No major skill gaps detected. Focus on projects and advanced topics.']
    return roadmap
