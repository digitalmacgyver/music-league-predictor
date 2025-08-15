#!/usr/bin/env ./venv/bin/python3
"""
Generate the voter similarity data for the insights document
"""

import logging
from voter_preferences import VoterPreferenceModeler
import numpy as np

def generate_similarity_insights():
    """Generate detailed similarity data for all voters"""
    
    logging.basicConfig(level=logging.WARNING)
    modeler = VoterPreferenceModeler()
    
    try:
        # Load data
        print("Loading voter data...")
        df = modeler.load_voting_data()
        modeler.build_voter_song_matrix(df)
        modeler.build_voter_profiles(df)
        modeler.calculate_voter_similarity()
        
        print("\nVOTER SIMILARITY ANALYSIS")
        print("=" * 50)
        
        # For each voter, find most and least similar
        for i, voter in enumerate(modeler.voters):
            similarities = modeler.similarity_matrix[i]
            
            # Find most similar (excluding self)
            most_similar_idx = None
            most_similar_score = -1
            for j, score in enumerate(similarities):
                if i != j and score > most_similar_score:
                    most_similar_score = score
                    most_similar_idx = j
            
            # Find least similar (excluding self)
            least_similar_idx = None
            least_similar_score = 2  # Start high since scores are 0-1
            for j, score in enumerate(similarities):
                if i != j and score < least_similar_score:
                    least_similar_score = score
                    least_similar_idx = j
            
            most_similar_voter = modeler.voters[most_similar_idx] if most_similar_idx is not None else "N/A"
            least_similar_voter = modeler.voters[least_similar_idx] if least_similar_idx is not None else "N/A"
            
            print(f"| **{voter}** | {most_similar_voter} | {most_similar_score:.3f} | {least_similar_voter} | {least_similar_score:.3f} |")
        
        # Find overall extremes
        print(f"\n\nOVERALL STATISTICS")
        print("-" * 30)
        
        max_similarity = 0
        max_pair = None
        min_similarity = 1
        min_pair = None
        
        for i in range(len(modeler.voters)):
            for j in range(i+1, len(modeler.voters)):
                similarity = modeler.similarity_matrix[i][j]
                if similarity > max_similarity:
                    max_similarity = similarity
                    max_pair = (modeler.voters[i], modeler.voters[j])
                if similarity < min_similarity:
                    min_similarity = similarity
                    min_pair = (modeler.voters[i], modeler.voters[j])
        
        print(f"Highest similarity: {max_pair[0]} & {max_pair[1]} ({max_similarity:.3f})")
        print(f"Lowest similarity: {min_pair[0]} & {min_pair[1]} ({min_similarity:.3f})")
        
        # Calculate average
        total_similarities = []
        for i in range(len(modeler.voters)):
            for j in range(i+1, len(modeler.voters)):
                total_similarities.append(modeler.similarity_matrix[i][j])
        
        avg_similarity = np.mean(total_similarities)
        print(f"Average similarity: {avg_similarity:.3f}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        modeler.close()

if __name__ == "__main__":
    generate_similarity_insights()