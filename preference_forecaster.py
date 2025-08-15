#!/usr/bin/env ./venv/bin/python3
"""
Group Preference Forecasting Model

Predicts how group preferences will evolve based on:
- Historical turnover patterns
- Voter composition changes  
- Preference shift trends
- Core vs transient voter influence
"""

import numpy as np
import pandas as pd
from setup_db import get_db_connection
from historical_patterns import HistoricalPatternAnalyzer
import re
from collections import defaultdict

class GroupPreferenceForecaster:
    """Forecasts group preference evolution based on voter pool composition"""
    
    def __init__(self):
        self.analyzer = HistoricalPatternAnalyzer()
        self.models = {}
        self.voter_influence_scores = {}
    
    def calculate_voter_influence_scores(self):
        """Calculate how much each voter type influences group preferences"""
        
        # Load historical data
        results = self.analyzer.generate_comprehensive_report()
        voter_classifications = results['voter_classifications']
        voter_evolution = results['voter_evolution']
        preference_trends = results['preference_trends']
        
        # Calculate influence based on participation and scoring patterns
        influence_scores = {}
        
        for _, voter in voter_classifications.iterrows():
            name = voter['voter']
            participation_rate = voter['leagues_participated'] / len(preference_trends)
            voter_type = voter['voter_type']
            avg_score = voter['avg_score']
            
            # Base influence on participation and consistency
            base_influence = participation_rate * voter['total_votes']
            
            # Adjust for voter type
            type_multipliers = {
                'core': 1.5,      # Core voters have higher influence
                'regular': 1.0,   # Regular voters have normal influence  
                'transient': 0.3  # Transient voters have lower influence
            }
            
            influence = base_influence * type_multipliers.get(voter_type, 1.0)
            
            influence_scores[name] = {
                'influence': influence,
                'voter_type': voter_type,
                'avg_score': avg_score,
                'participation_rate': participation_rate,
                'generosity_factor': avg_score - preference_trends['avg_rating'].mean()
            }
        
        self.voter_influence_scores = influence_scores
        return influence_scores
    
    def build_turnover_impact_model(self):
        """Build model predicting impact of voter turnover on preferences"""
        
        results = self.analyzer.generate_comprehensive_report()
        impact_analysis = results['impact_analysis']
        
        # Analyze correlation between turnover and preference changes
        turnover_rates = impact_analysis['turnover_rate'].values
        score_changes = impact_analysis['score_change'].values
        
        # Simple linear relationship
        correlation = np.corrcoef(turnover_rates, score_changes)[0,1]
        
        # Calculate average impact per turnover percentage
        avg_impact_per_turnover = np.mean(score_changes) / np.mean(turnover_rates)
        
        self.models['turnover_impact'] = {
            'correlation': correlation,
            'avg_impact_per_turnover': avg_impact_per_turnover,
            'baseline_volatility': np.std(score_changes)
        }
        
        return self.models['turnover_impact']
    
    def predict_preference_shift(self, departing_voters=None, new_voters=None, 
                               new_voter_profiles=None, target_league_theme=None):
        """Predict how preferences will shift given voter changes"""
        
        if not self.voter_influence_scores:
            self.calculate_voter_influence_scores()
        
        if 'turnover_impact' not in self.models:
            self.build_turnover_impact_model()
        
        departing_voters = departing_voters or []
        new_voters = new_voters or []
        new_voter_profiles = new_voter_profiles or {}
        
        # Calculate current group composition
        current_voters = set(self.voter_influence_scores.keys())
        remaining_voters = current_voters - set(departing_voters)
        
        # Calculate weighted influence loss from departing voters
        lost_influence = sum(self.voter_influence_scores[voter]['influence'] 
                           for voter in departing_voters 
                           if voter in self.voter_influence_scores)
        
        lost_generosity = sum(self.voter_influence_scores[voter]['generosity_factor'] * 
                            self.voter_influence_scores[voter]['influence']
                            for voter in departing_voters 
                            if voter in self.voter_influence_scores)
        
        # Calculate remaining group characteristics
        remaining_influence = sum(self.voter_influence_scores[voter]['influence'] 
                                for voter in remaining_voters)
        
        remaining_generosity = sum(self.voter_influence_scores[voter]['generosity_factor'] * 
                                 self.voter_influence_scores[voter]['influence']
                                 for voter in remaining_voters)
        
        # Estimate new voter impact (assume average if no profile given)
        avg_new_voter_influence = np.mean([v['influence'] for v in self.voter_influence_scores.values()]) * 0.5  # New voters start with reduced influence
        avg_new_voter_generosity = 0.0  # Assume neutral until proven otherwise
        
        new_voter_influence = len(new_voters) * avg_new_voter_influence
        new_voter_generosity = len(new_voters) * avg_new_voter_generosity
        
        # Apply any specific new voter profiles
        for voter, profile in new_voter_profiles.items():
            if voter in new_voters:
                new_voter_generosity += profile.get('expected_generosity', 0) * avg_new_voter_influence
        
        # Calculate total new composition
        total_influence = remaining_influence + new_voter_influence
        total_generosity = remaining_generosity + new_voter_generosity
        
        # Predict preference shift
        if total_influence > 0:
            expected_generosity_shift = (total_generosity / total_influence) - (remaining_generosity / remaining_influence if remaining_influence > 0 else 0)
        else:
            expected_generosity_shift = 0
        
        # Calculate turnover rate and apply turnover model
        turnover_rate = len(new_voters) / (len(remaining_voters) + len(new_voters)) if remaining_voters or new_voters else 0
        turnover_impact = turnover_rate * self.models['turnover_impact']['avg_impact_per_turnover']
        
        # Combine effects
        total_predicted_shift = expected_generosity_shift + turnover_impact
        
        # Estimate confidence based on data quality
        confidence = min(1.0, remaining_influence / (remaining_influence + new_voter_influence))
        
        return {
            'predicted_generosity_shift': total_predicted_shift,
            'confidence': confidence,
            'turnover_rate': turnover_rate,
            'departing_voter_impact': lost_influence,
            'new_voter_count': len(new_voters),
            'remaining_core_voters': len([v for v in remaining_voters 
                                        if v in self.voter_influence_scores and 
                                        self.voter_influence_scores[v]['voter_type'] == 'core']),
            'prediction_factors': {
                'composition_shift': expected_generosity_shift,
                'turnover_impact': turnover_impact,
                'baseline_volatility': self.models['turnover_impact']['baseline_volatility']
            }
        }
    
    def forecast_league_success_probability(self, song_candidates, voter_composition_prediction):
        """Forecast success probability for songs given predicted voter composition"""
        
        base_success_rates = {
            'conservative_group': {'threshold': 1.5, 'high_threshold': 2.0},
            'generous_group': {'threshold': 1.2, 'high_threshold': 1.8},
            'mixed_group': {'threshold': 1.3, 'high_threshold': 1.9}
        }
        
        # Determine group type from prediction
        predicted_shift = voter_composition_prediction['predicted_generosity_shift']
        
        if predicted_shift < -0.2:
            group_type = 'conservative_group'
        elif predicted_shift > 0.2:
            group_type = 'generous_group'
        else:
            group_type = 'mixed_group'
        
        thresholds = base_success_rates[group_type]
        
        forecasts = []
        for song in song_candidates:
            # This would integrate with our existing scoring system
            # For now, simulate based on song characteristics
            
            estimated_score = song.get('predicted_score', 1.5)  # Would come from our forecasting system
            
            success_probability = min(1.0, max(0.0, 
                (estimated_score - thresholds['threshold']) / 
                (thresholds['high_threshold'] - thresholds['threshold'])))
            
            forecasts.append({
                'song': song,
                'success_probability': success_probability,
                'estimated_score': estimated_score,
                'group_type': group_type,
                'confidence': voter_composition_prediction['confidence']
            })
        
        return sorted(forecasts, key=lambda x: x['success_probability'], reverse=True)
    
    def generate_strategic_recommendations(self, upcoming_league_info=None):
        """Generate strategic recommendations based on preference forecasting"""
        
        if not self.voter_influence_scores:
            self.calculate_voter_influence_scores()
        
        print("="*80)
        print("      GROUP PREFERENCE FORECASTING RECOMMENDATIONS")
        print("="*80)
        
        # Analyze current composition
        core_voters = [name for name, data in self.voter_influence_scores.items() 
                      if data['voter_type'] == 'core']
        regular_voters = [name for name, data in self.voter_influence_scores.items() 
                         if data['voter_type'] == 'regular']
        
        print(f"\nCurrent Group Composition:")
        print(f"  Core voters: {len(core_voters)} ({', '.join(core_voters[:5])}{'...' if len(core_voters) > 5 else ''})")
        print(f"  Regular voters: {len(regular_voters)}")
        print(f"  Expected turnover: ~40% (historical average)")
        
        # Calculate current group tendencies
        avg_generosity = np.mean([data['generosity_factor'] for data in self.voter_influence_scores.values()])
        
        if avg_generosity > 0.1:
            group_tendency = "generous"
        elif avg_generosity < -0.1:
            group_tendency = "conservative"
        else:
            group_tendency = "balanced"
        
        print(f"  Current tendency: {group_tendency} (avg generosity factor: {avg_generosity:+.2f})")
        
        # Strategic recommendations
        print(f"\n" + "-"*80)
        print("STRATEGIC RECOMMENDATIONS")
        print("-"*80)
        
        if group_tendency == "conservative":
            print(f"\nFor Conservative Groups:")
            print(f"  • Focus on exceptional quality over mass appeal")
            print(f"  • Target songs that core voters (especially Joe Hayward, Matt M) would appreciate")
            print(f"  • Avoid experimental or polarizing selections")
            print(f"  • Theme adherence is critical - poor fits will be penalized heavily")
        
        elif group_tendency == "generous":
            print(f"\nFor Generous Groups:")
            print(f"  • Broader range of songs can succeed")
            print(f"  • Creative interpretations of themes may be rewarded")
            print(f"  • Focus on songs with wide appeal rather than niche excellence")
            print(f"  • Nostalgic or emotionally resonant tracks perform well")
        
        else:
            print(f"\nFor Balanced Groups:")
            print(f"  • Mix of quality and appeal strategies")
            print(f"  • Test both safe and creative approaches")
            print(f"  • Monitor early round results to adjust strategy")
            print(f"  • Consider voter-specific targeting for key participants")
        
        # Voter-specific insights
        print(f"\n" + "-"*80)
        print("HIGH-INFLUENCE VOTER INSIGHTS")
        print("-"*80)
        
        high_influence = sorted(self.voter_influence_scores.items(), 
                              key=lambda x: x[1]['influence'], reverse=True)[:5]
        
        for name, data in high_influence:
            influence_score = data['influence']
            generosity = data['generosity_factor']
            voter_type = data['voter_type']
            
            print(f"\n{name} ({voter_type}):")
            print(f"  Influence score: {influence_score:.1f}")
            print(f"  Scoring tendency: {generosity:+.2f} vs group average")
            
            if generosity > 0.2:
                print(f"  Strategy: Broad appeal songs, emotional connection")
            elif generosity < -0.2:
                print(f"  Strategy: High quality, exceptional tracks only")
            else:
                print(f"  Strategy: Balanced approach, focus on theme fit")
        
        # Scenario planning
        print(f"\n" + "-"*80)
        print("SCENARIO PLANNING")
        print("-"*80)
        
        # High turnover scenario
        high_turnover_prediction = self.predict_preference_shift(
            departing_voters=['someben', 'Qui-Jon Jinn'],  # Example departures
            new_voters=['NewVoter1', 'NewVoter2', 'NewVoter3']  # Example new voters
        )
        
        print(f"\nHigh Turnover Scenario (40%+ new voters):")
        print(f"  Predicted generosity shift: {high_turnover_prediction['predicted_generosity_shift']:+.2f}")
        print(f"  Confidence: {high_turnover_prediction['confidence']:.1%}")
        print(f"  Recommendation: {'More conservative song selection' if high_turnover_prediction['predicted_generosity_shift'] < 0 else 'Broader song selection possible'}")
        
        # Stable composition scenario  
        stable_prediction = self.predict_preference_shift(
            departing_voters=[],  # No departures
            new_voters=['NewVoter1']  # Minimal turnover
        )
        
        print(f"\nStable Composition Scenario (<20% turnover):")
        print(f"  Predicted generosity shift: {stable_prediction['predicted_generosity_shift']:+.2f}")
        print(f"  Confidence: {stable_prediction['confidence']:.1%}")
        print(f"  Recommendation: Current strategies should remain effective")
        
        return {
            'current_tendency': group_tendency,
            'high_influence_voters': high_influence,
            'scenario_predictions': {
                'high_turnover': high_turnover_prediction,
                'stable': stable_prediction
            }
        }

if __name__ == "__main__":
    forecaster = GroupPreferenceForecaster()
    recommendations = forecaster.generate_strategic_recommendations()