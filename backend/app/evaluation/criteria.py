from typing import Dict, Any

CRITERIA_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "relevance": {
        "name": "Relevance",
        "description": "Does the response directly and comprehensively address the user's specific query without extraneous deviation?",
        "min": 0.0,
        "max": 10.0,
        "default_weight": 0.25
    },
    "correctness": {
        "name": "Correctness",
        "description": "Are all stated claims, facts, technical explanations, and logic mathematically and empirically accurate?",
        "min": 0.0,
        "max": 10.0,
        "default_weight": 0.25
    },
    "completeness": {
        "name": "Completeness",
        "description": "Does the response sufficiently cover all core facets, nuances, and edge cases implied by the query?",
        "min": 0.0,
        "max": 10.0,
        "default_weight": 0.15
    },
    "clarity": {
        "name": "Clarity & Structure",
        "description": "Is the response coherent, well-structured, easy to read, and logically sequenced?",
        "min": 0.0,
        "max": 10.0,
        "default_weight": 0.15
    },
    "consistency": {
        "name": "Internal Consistency",
        "description": "Is the response internally harmonious and free from self-contradictions or conflicting terminology?",
        "min": 0.0,
        "max": 10.0,
        "default_weight": 0.05
    },
    "preference_match": {
        "name": "User Preference Match",
        "description": "How closely does the response adhere to the user's explicit style, tone, formality, and target depth preferences?",
        "min": 0.0,
        "max": 10.0,
        "default_weight": 0.10
    },
    "conciseness": {
        "name": "Conciseness",
        "description": "Does the response avoid unnecessary filler, repetitive phrasing, and bloated prose?",
        "min": 0.0,
        "max": 10.0,
        "default_weight": 0.05
    },
    "technical_depth": {
        "name": "Technical Depth",
        "description": "Does the response exhibit appropriate architectural, algorithmic, or mechanical rigor appropriate for the query?",
        "min": 0.0,
        "max": 10.0,
        "default_weight": 0.0
    }
}
