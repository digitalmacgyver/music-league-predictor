#!/usr/bin/env ./venv/bin/python3
"""
Test vote parsing logic with the actual data we found
"""

import re

def parse_vote_data(footer_text):
    """Parse the vote data from card-footer text"""
    print("Raw footer text:")
    print(repr(footer_text))
    print("\n" + "="*60)
    
    # The format appears to be: voter | comment | points | voter | comment | points...
    # Let's split by | and group into triplets
    parts = [p.strip() for p in footer_text.split('|')]
    print(f"Split into {len(parts)} parts:")
    for i, part in enumerate(parts):
        print(f"  {i}: '{part}'")
    
    votes = []
    i = 0
    while i < len(parts):
        # Look for a pattern: voter_name | optional_comment | points
        if i + 2 < len(parts):
            voter = parts[i]
            comment_or_points = parts[i + 1]
            next_part = parts[i + 2]
            
            # Check if comment_or_points is actually points (just a number)
            if re.match(r'^\d+$', comment_or_points.strip()):
                # No comment, just points
                points = int(comment_or_points)
                comment = ""
                i += 2
            elif re.match(r'^\d+$', next_part.strip()):
                # Has comment and points
                comment = comment_or_points
                points = int(next_part)
                i += 3
            else:
                # Unclear pattern, skip
                i += 1
                continue
                
            votes.append({
                'voter': voter,
                'comment': comment,
                'points': points
            })
        else:
            break
    
    return votes

# Test with the actual footer text we found
footer_text = "caliban | As someone who submitted The Wreck of the Edmund Fitzgerald in a previous league, I would probably give his answering machine a point. | 3 | Rachel Peterson | Will always upvote gordon lightfoot | 2 | William Strickland Hamilton | Such a great tune | 2 | Adam Gimpert | Got the sound. | 1 | someben | 1 | Joe Hayward | Man, Gordon's awesome.  The amount of menace he puts into that refrain is impressive. | 1 | Jared | 1 | Qui-Jon Jinn | 1 | Matt M | 1 | Drew | I don't love this, but I do like it and you get my token 'folk' point this week. | 1 | legion1996a | This is pretty great! | 1"

votes = parse_vote_data(footer_text)
print(f"\nParsed {len(votes)} votes:")
total_points = 0
for vote in votes:
    print(f"  {vote['voter']}: {vote['points']} points - '{vote['comment']}'")
    total_points += vote['points']

print(f"\nTotal points calculated: {total_points}")