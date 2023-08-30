import sys
import pandas as pd
from typing import *
from collections import defaultdict

HARD_MATCH_COLUMNS = []
SOFT_MATCH_COLUMNS = ['Secondary Preference ', 'Primary Hobbies', 'Secondary Hobbies']

def filter_for_regional_langs(langs: List[str], hard_filter: bool=False):
    if len(langs) > 1 or hard_filter:
        return [lang for lang in langs if lang not in ["hindi", "english"]]
    return langs

def compute_mentoring_match(mentor_row, mentee_row, eps: float=0.01, hobby_match_tol: float=0.05):
    """score the appropriateness of a mentor for a mentee
    
    - hobby_match_tol: The minimum amount of hobby overlap to trigger consideration of secondary language overlap.
    """
    if isinstance(mentor_row[SOFT_MATCH_COLUMNS[0]], float):
        mentor_row[SOFT_MATCH_COLUMNS[0]] = ""
    if isinstance(mentee_row[SOFT_MATCH_COLUMNS[0]], float):
        mentee_row[SOFT_MATCH_COLUMNS[0]] = ""
    
    mentor_primary_langs = filter_for_regional_langs([lang.strip().lower() for lang in mentor_row[HARD_MATCH_COLUMNS[0]].split(",")])
    mentee_primary_langs = filter_for_regional_langs([lang.strip().lower() for lang in mentee_row[HARD_MATCH_COLUMNS[0]].split(",")])
    
    mentor_secondary_langs = filter_for_regional_langs([lang.strip().lower() for lang in mentor_row[SOFT_MATCH_COLUMNS[0]].split(",")], hard_filter=True)
    mentee_secondary_langs = filter_for_regional_langs([lang.strip().lower() for lang in mentee_row[SOFT_MATCH_COLUMNS[0]].split(",")], hard_filter=True)
    
    lang_match = int(len(set(mentor_primary_langs).intersection(set(mentee_primary_langs))) > 0)
    gender_match = int(mentor_row[HARD_MATCH_COLUMNS[1]] == mentee_row[HARD_MATCH_COLUMNS[1]])
    
    common_langs = ", ".join(set(mentor_primary_langs).intersection(set(mentee_primary_langs)))
    common_secondary_langs = ", ".join(set(mentor_secondary_langs).intersection(set(mentee_secondary_langs)))

    try: sec_lang_match = len(set(mentor_secondary_langs).intersection(set(mentee_secondary_langs)))/len(set(mentee_secondary_langs))
    except ZeroDivisionError: sec_lang_match = eps
    if sec_lang_match == 0: sec_lang_match = eps
    
    mentor_hobbies = [hobby.strip().lower() for hobby in mentor_row[SOFT_MATCH_COLUMNS[1]].split(",")+ mentor_row[SOFT_MATCH_COLUMNS[2]].split(",")]
    mentee_hobbies = [hobby.strip().lower() for hobby in mentee_row[SOFT_MATCH_COLUMNS[1]].split(",")+mentee_row[SOFT_MATCH_COLUMNS[2]].split(",")]
    hobby_match = len(set(mentor_hobbies).intersection(set(mentee_hobbies)))/len(set(mentee_hobbies))

    hard_score = lang_match * gender_match
    reason = ""
    
    if hard_score == 1:
        reason += f" Both are same gender and speak {common_langs}."
    common_hobbies = "'"+"', '".join(set(mentor_hobbies).intersection(set(mentee_hobbies)))+"'"
    if hobby_match >= hobby_match_tol:
        soft_score = hobby_match
        reason += f" Their common hobbies are: {common_hobbies} ({len(set(mentor_hobbies).intersection(set(mentee_hobbies)))}/{len(mentee_hobbies)})"
    else:
        reason += f" They only have {common_hobbies} ({len(set(mentor_hobbies).intersection(set(mentee_hobbies)))}/{len(mentee_hobbies)}) as common hobbies, but speak {common_secondary_langs} as secondary languages."
        
    soft_score = hobby_match if hobby_match >= hobby_match_tol else max(sec_lang_match, hobby_match)

    return hard_score, soft_score, hard_score + soft_score, reason.strip()

# main
if __name__ == "__main__":
    path = sys.argv[1]
    data = pd.read_csv(path).to_dict("records")
    columns = list(data[0].keys())
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
            hard_score, soft_score, total_score, reason = compute_mentoring_match(mentor, mentee)
            mentoring_match_scores[mentor_name] = [total_score, reason]
        mentoring_matches = sorted(mentoring_match_scores.items(), key=lambda x: x[1][0], reverse=True)
        assigned_mentor = mentoring_matches[0][0]
        assigned_mentor_gender = mentor_to_row[assigned_mentor]["Gender"]
        assigned_mentor_hobbies = mentor_to_row[assigned_mentor][SOFT_MATCH_COLUMNS[0]] + ", " + mentor_to_row[assigned_mentor][SOFT_MATCH_COLUMNS[1]]
        mentee_hobbies = mentee[SOFT_MATCH_COLUMNS[0]] + ", " + mentee[SOFT_MATCH_COLUMNS[1]]
        assigning_reason = mentoring_matches[0][1][1]
        assigning_score = mentoring_matches[0][1][0]
        mentor_load[assigned_mentor] += 1
        # print(mentee["Name "], mentoring_matches[:2])
        mentor_mentee_assignment.append({
            "Mentee": mentee["Name "], 
            "Mentee Gender": mentee["Gender"], 
            "Mentor": assigned_mentor, 
            "Mentor Gender": assigned_mentor_gender, 
            "Reason": assigning_reason, 
            "Score": assigning_score,
            "Mentor Hobbies": assigned_mentor_hobbies, 
            "Mentee Hobbies": mentee_hobbies, 
            "Mentor Primary Lang(s)": mentor_to_row[assigned_mentor][HARD_MATCH_COLUMNS[0]], 
            "Mentee Primary Lang(s)": mentee[HARD_MATCH_COLUMNS[0]]
        })
        if mentor_load[assigned_mentor] == 3:
            del mentor_to_row[assigned_mentor]
    df = pd.DataFrame(mentor_mentee_assignment)
    df.to_csv("assignment.csv", index=False)