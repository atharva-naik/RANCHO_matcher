import sys
import pandas as pd
from typing import *
from collections import defaultdict

HARD_MATCH_COLUMNS = [] #["""Primary Preference 
# Please select the most preferred language only. If you are equally comfortable in 2 languages (example - in both Hindi and a native language), you can select both options.
# '""", "Gender"]
SOFT_MATCH_COLUMNS = ['Secondary Preference ', 'Primary Hobbies', 'Secondary Hobbies']

def filter_for_regional_langs(langs: List[str]):
    if len(langs) > 1:
        return [lang for lang in langs if lang not in ["hindi", "english"]]
    return langs

def compute_mentoring_match(mentor_row, mentee_row, eps: float=0.01):
    """score the appropriateness of a mentor for a mentee"""
    if isinstance(mentor_row[SOFT_MATCH_COLUMNS[0]], float):
        mentor_row[SOFT_MATCH_COLUMNS[0]] = ""
    if isinstance(mentee_row[SOFT_MATCH_COLUMNS[0]], float):
        mentee_row[SOFT_MATCH_COLUMNS[0]] = ""
    mentor_primary_langs = filter_for_regional_langs([lang.strip().lower() for lang in mentor_row[HARD_MATCH_COLUMNS[0]].split(",")])
    mentee_primary_langs = filter_for_regional_langs([lang.strip().lower() for lang in mentee_row[HARD_MATCH_COLUMNS[0]].split(",")])
    mentor_secondary_langs = filter_for_regional_langs([lang.strip().lower() for lang in mentor_row[SOFT_MATCH_COLUMNS[0]].split(",")])
    mentee_secondary_langs = filter_for_regional_langs([lang.strip().lower() for lang in mentee_row[SOFT_MATCH_COLUMNS[0]].split(",")])
    lang_match = int(len(set(mentor_primary_langs).intersection(set(mentee_primary_langs))) > 0)
    gender_match = int(mentor_row[HARD_MATCH_COLUMNS[1]] == mentee_row[HARD_MATCH_COLUMNS[1]])
    try: sec_lang_match = len(set(mentor_primary_langs).intersection(set(mentee_primary_langs)))/len(set(mentee_primary_langs))
    except ZeroDivisionError: sec_lang_match = eps
    if sec_lang_match == 0: sec_lang_match = eps
    hard_score = lang_match * gender_match
    soft_score = sec_lang_match

    return hard_score, soft_score, hard_score + soft_score

# main
if __name__ == "__main__":
    path = sys.argv[1]
    data = pd.read_csv(path).to_dict("records")
    columns = list(data[0].keys())
    print(columns)
    HARD_MATCH_COLUMNS.append(columns[6])
    HARD_MATCH_COLUMNS.append(columns[5])
    mentors = [rec for rec in data if rec["role"] == "mentor"]
    mentees = [rec for rec in data if rec["role"] == "mentee"]
    mentor_load = defaultdict(lambda: 0)
    mentor_to_row = {mentor["Name "]: mentor for mentor in mentors}
    mentor_mentee_assignment = []
    for mentee in mentees:
        mentoring_match_scores = {}
        for mentor_name, mentor in mentor_to_row.items():
            hard_score, soft_score, total_score = compute_mentoring_match(mentor, mentee)
            mentoring_match_scores[mentor_name] = total_score
        mentoring_matches = sorted(mentoring_match_scores.items(), key=lambda x: x[1], reverse=True)
        assigned_mentor = mentoring_matches[0][0]
        mentor_load[assigned_mentor] += 1
        if mentor_load[assigned_mentor] == 3:
            del mentor_to_row[assigned_mentor]
        # print(mentee["Name "], mentoring_matches[:2])
        mentor_mentee_assignment.append({"Mentee": mentee["Name "], "Mentor": assigned_mentor, "Reason": ""})
    df = pd.DataFrame(mentor_mentee_assignment)