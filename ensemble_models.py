#!/usr/bin/env ./venv/bin/python3
"""
Ensemble Prediction Models for Music League

Combines multiple scoring approaches into sophisticated ensemble models:
- Weighted ensemble with optimal weights
- Stacked meta-learning models
- Dynamic confidence-based weighting
- Voting systems for robust predictions
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class PredictionComponent:
    """Individual prediction component with confidence"""
    name: str
    score: float
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = None

@dataclass
class EnsemblePrediction:
    """Final ensemble prediction with component breakdown"""
    final_score: float
    confidence: float
    components: List[PredictionComponent]
    ensemble_method: str
    reasoning: str
    metadata: Dict[str, Any] = None

class BaseEnsembleModel(ABC):
    """Base class for ensemble prediction models"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_trained = False
        
    @abstractmethod
    def fit(self, predictions: List[List[PredictionComponent]], targets: List[float]):
        """Train the ensemble model"""
        pass
    
    @abstractmethod
    def predict(self, predictions: List[PredictionComponent]) -> EnsemblePrediction:
        """Make ensemble prediction"""
        pass

class WeightedEnsemble(BaseEnsembleModel):
    """Weighted combination of predictions with learned optimal weights"""
    
    def __init__(self, method: str = 'ridge'):
        super().__init__(f"WeightedEnsemble_{method}")
        self.method = method
        self.weights = {}
        self.intercept = 0.0
        self.component_names = []
        
    def fit(self, predictions: List[List[PredictionComponent]], targets: List[float]):
        """Learn optimal weights for combining predictions"""
        
        if not predictions or not targets:
            raise ValueError("Need training data to fit ensemble")
        
        # Extract component names from first prediction
        self.component_names = [comp.name for comp in predictions[0]]
        
        # Build feature matrix: [n_samples, n_components]
        X = []
        for pred_list in predictions:
            scores = [comp.score for comp in pred_list]
            X.append(scores)
        
        X = np.array(X)
        y = np.array(targets)
        
        # Fit model to learn optimal weights
        if self.method == 'ridge':
            model = Ridge(alpha=1.0, positive=True)  # Positive weights only
        elif self.method == 'linear':
            model = LinearRegression(positive=True)
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        model.fit(X, y)
        
        # Store weights
        self.weights = dict(zip(self.component_names, model.coef_))
        self.intercept = model.intercept_
        self.is_trained = True
        
        # Calculate cross-validation score (only if enough samples)
        if len(X) >= 5:
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
            self.cv_rmse = np.sqrt(-cv_scores.mean())
        else:
            # Use simple train error for small datasets
            y_pred = model.predict(X)
            self.cv_rmse = np.sqrt(mean_squared_error(y, y_pred))
        
        logger.info(f"Trained {self.name} with weights: {self.weights}")
        logger.info(f"Cross-validation RMSE: {self.cv_rmse:.3f}")
        
    def predict(self, predictions: List[PredictionComponent]) -> EnsemblePrediction:
        """Make weighted ensemble prediction"""
        
        if not self.is_trained:
            # Fall back to simple average if not trained
            scores = [comp.score for comp in predictions]
            weights = {comp.name: 1.0/len(predictions) for comp in predictions}
            final_score = np.mean(scores)
            confidence = 0.5  # Low confidence for untrained model
        else:
            # Use learned weights
            weighted_sum = self.intercept
            total_weight = 0.0
            
            for comp in predictions:
                if comp.name in self.weights:
                    weight = self.weights[comp.name]
                    weighted_sum += weight * comp.score
                    total_weight += weight
            
            final_score = weighted_sum
            weights = self.weights
            
            # Calculate confidence based on component agreement
            scores = [comp.score for comp in predictions]
            score_std = np.std(scores)
            confidence = max(0.1, min(0.95, 1.0 - score_std))
        
        # Generate reasoning
        reasoning = f"Weighted combination: "
        for comp in predictions:
            if comp.name in weights:
                weight = weights[comp.name]
                reasoning += f"{comp.name}({weight:.2f}) "
        
        return EnsemblePrediction(
            final_score=final_score,
            confidence=confidence,
            components=predictions,
            ensemble_method=self.name,
            reasoning=reasoning,
            metadata={'weights': weights, 'intercept': self.intercept}
        )

class StackedEnsemble(BaseEnsembleModel):
    """Stacked ensemble using meta-learner to combine predictions"""
    
    def __init__(self, meta_model_type: str = 'rf'):
        super().__init__(f"StackedEnsemble_{meta_model_type}")
        self.meta_model_type = meta_model_type
        self.meta_model = None
        self.component_names = []
        
    def fit(self, predictions: List[List[PredictionComponent]], targets: List[float]):
        """Train meta-model to combine component predictions"""
        
        if not predictions or not targets:
            raise ValueError("Need training data to fit ensemble")
        
        # Extract component names
        self.component_names = [comp.name for comp in predictions[0]]
        
        # Build feature matrix with scores and confidences
        X = []
        for pred_list in predictions:
            features = []
            for comp in pred_list:
                features.extend([comp.score, comp.confidence])
            X.append(features)
        
        X = np.array(X)
        y = np.array(targets)
        
        # Create meta-model
        if self.meta_model_type == 'rf':
            self.meta_model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif self.meta_model_type == 'ridge':
            self.meta_model = Ridge(alpha=1.0)
        else:
            raise ValueError(f"Unknown meta-model type: {self.meta_model_type}")
        
        # Train meta-model
        self.meta_model.fit(X, y)
        self.is_trained = True
        
        # Calculate performance metrics
        y_pred = self.meta_model.predict(X)
        self.train_rmse = np.sqrt(mean_squared_error(y, y_pred))
        
        # Feature importance for Random Forest
        if hasattr(self.meta_model, 'feature_importances_'):
            self.feature_importance = dict(zip(
                [f"{name}_{feat}" for name in self.component_names for feat in ['score', 'confidence']],
                self.meta_model.feature_importances_
            ))
        
        logger.info(f"Trained {self.name} with RMSE: {self.train_rmse:.3f}")
        
    def predict(self, predictions: List[PredictionComponent]) -> EnsemblePrediction:
        """Make stacked ensemble prediction"""
        
        if not self.is_trained:
            # Fall back to simple average
            scores = [comp.score for comp in predictions]
            final_score = np.mean(scores)
            confidence = 0.5
            reasoning = "Untrained model - using simple average"
        else:
            # Build feature vector
            features = []
            for comp in predictions:
                features.extend([comp.score, comp.confidence])
            
            X = np.array(features).reshape(1, -1)
            final_score = self.meta_model.predict(X)[0]
            
            # Calculate confidence based on model's training performance
            confidence = max(0.1, min(0.95, 1.0 - self.train_rmse / 5.0))
            
            reasoning = f"Meta-model ({self.meta_model_type}) prediction"
        
        return EnsemblePrediction(
            final_score=final_score,
            confidence=confidence,
            components=predictions,
            ensemble_method=self.name,
            reasoning=reasoning,
            metadata={'meta_model_type': self.meta_model_type}
        )

class DynamicWeightedEnsemble(BaseEnsembleModel):
    """Dynamic ensemble that adjusts weights based on component confidence"""
    
    def __init__(self, base_weights: Dict[str, float] = None):
        super().__init__("DynamicWeightedEnsemble")
        self.base_weights = base_weights or {}
        self.learned_weights = {}
        
    def fit(self, predictions: List[List[PredictionComponent]], targets: List[float]):
        """Learn base weights and confidence scaling"""
        
        # First, learn base weights like weighted ensemble
        weighted_ensemble = WeightedEnsemble('ridge')
        weighted_ensemble.fit(predictions, targets)
        self.learned_weights = weighted_ensemble.weights
        self.is_trained = True
        
        logger.info(f"Trained {self.name} with base weights: {self.learned_weights}")
        
    def predict(self, predictions: List[PredictionComponent]) -> EnsemblePrediction:
        """Make prediction with dynamic confidence-based weighting"""
        
        # Start with learned weights or equal weights
        if self.is_trained:
            base_weights = self.learned_weights
        else:
            base_weights = {comp.name: 1.0 for comp in predictions}
        
        # Adjust weights based on component confidence
        dynamic_weights = {}
        total_weight = 0.0
        
        for comp in predictions:
            base_weight = base_weights.get(comp.name, 1.0)
            # Scale by confidence: high confidence gets more weight
            dynamic_weight = base_weight * (0.5 + comp.confidence)
            dynamic_weights[comp.name] = dynamic_weight
            total_weight += dynamic_weight
        
        # Normalize weights
        if total_weight > 0:
            dynamic_weights = {name: weight/total_weight for name, weight in dynamic_weights.items()}
        
        # Calculate weighted prediction
        final_score = sum(comp.score * dynamic_weights.get(comp.name, 0) for comp in predictions)
        
        # Calculate overall confidence as weighted average of component confidences
        confidence = sum(comp.confidence * dynamic_weights.get(comp.name, 0) for comp in predictions)
        
        reasoning = f"Dynamic weighting: "
        for comp in predictions:
            weight = dynamic_weights.get(comp.name, 0)
            reasoning += f"{comp.name}({weight:.2f}) "
        
        return EnsemblePrediction(
            final_score=final_score,
            confidence=confidence,
            components=predictions,
            ensemble_method=self.name,
            reasoning=reasoning,
            metadata={'dynamic_weights': dynamic_weights}
        )

class VotingEnsemble(BaseEnsembleModel):
    """Voting ensemble using multiple individual ensemble models"""
    
    def __init__(self, ensemble_models: List[BaseEnsembleModel] = None):
        super().__init__("VotingEnsemble")
        self.ensemble_models = ensemble_models or [
            WeightedEnsemble('ridge'),
            StackedEnsemble('rf'),
            DynamicWeightedEnsemble()
        ]
        
    def fit(self, predictions: List[List[PredictionComponent]], targets: List[float]):
        """Train all constituent ensemble models"""
        
        for model in self.ensemble_models:
            try:
                model.fit(predictions, targets)
                logger.info(f"Successfully trained {model.name}")
            except Exception as e:
                logger.warning(f"Failed to train {model.name}: {e}")
        
        self.is_trained = True
        
    def predict(self, predictions: List[PredictionComponent]) -> EnsemblePrediction:
        """Get predictions from all models and vote"""
        
        ensemble_predictions = []
        
        for model in self.ensemble_models:
            try:
                pred = model.predict(predictions)
                ensemble_predictions.append(pred)
            except Exception as e:
                logger.warning(f"Failed to get prediction from {model.name}: {e}")
        
        if not ensemble_predictions:
            # Fallback to simple average
            scores = [comp.score for comp in predictions]
            final_score = np.mean(scores)
            confidence = 0.5
            reasoning = "Voting ensemble failed - using simple average"
        else:
            # Weight by confidence and take average
            total_weighted_score = 0.0
            total_confidence_weight = 0.0
            
            for pred in ensemble_predictions:
                weight = pred.confidence
                total_weighted_score += pred.final_score * weight
                total_confidence_weight += weight
            
            if total_confidence_weight > 0:
                final_score = total_weighted_score / total_confidence_weight
                confidence = total_confidence_weight / len(ensemble_predictions)
            else:
                scores = [pred.final_score for pred in ensemble_predictions]
                final_score = np.mean(scores)
                confidence = 0.5
            
            reasoning = f"Voting ensemble ({len(ensemble_predictions)} models)"
        
        return EnsemblePrediction(
            final_score=final_score,
            confidence=confidence,
            components=predictions,
            ensemble_method=self.name,
            reasoning=reasoning,
            metadata={'ensemble_predictions': ensemble_predictions}
        )

class EnsembleManager:
    """Manages multiple ensemble models and selects best approach"""
    
    def __init__(self):
        self.models = {
            'weighted_ridge': WeightedEnsemble('ridge'),
            'weighted_linear': WeightedEnsemble('linear'),
            'stacked_rf': StackedEnsemble('rf'),
            'stacked_ridge': StackedEnsemble('ridge'),
            'dynamic': DynamicWeightedEnsemble(),
            'voting': VotingEnsemble()
        }
        self.best_model = None
        self.model_performance = {}
        
    def train_all_models(self, predictions: List[List[PredictionComponent]], targets: List[float]):
        """Train all ensemble models and identify best performer"""
        
        logger.info("Training all ensemble models...")
        
        for name, model in self.models.items():
            try:
                model.fit(predictions, targets)
                
                # Evaluate model performance (simple in-sample for now)
                pred_scores = []
                for pred_list in predictions:
                    ensemble_pred = model.predict(pred_list)
                    pred_scores.append(ensemble_pred.final_score)
                
                rmse = np.sqrt(mean_squared_error(targets, pred_scores))
                mae = mean_absolute_error(targets, pred_scores)
                
                self.model_performance[name] = {
                    'rmse': rmse,
                    'mae': mae,
                    'model': model
                }
                
                logger.info(f"{name}: RMSE={rmse:.3f}, MAE={mae:.3f}")
                
            except Exception as e:
                logger.error(f"Failed to train {name}: {e}")
                self.model_performance[name] = {
                    'rmse': float('inf'),
                    'mae': float('inf'),
                    'model': model
                }
        
        # Select best model by RMSE
        if self.model_performance:
            best_name = min(self.model_performance.keys(), 
                           key=lambda x: self.model_performance[x]['rmse'])
            self.best_model = self.model_performance[best_name]['model']
            logger.info(f"Best model: {best_name} (RMSE: {self.model_performance[best_name]['rmse']:.3f})")
        
    def predict(self, predictions: List[PredictionComponent], model_name: str = None) -> EnsemblePrediction:
        """Make prediction using specified model or best model"""
        
        if model_name and model_name in self.models:
            model = self.models[model_name]
        elif self.best_model:
            model = self.best_model
        else:
            # Fallback to voting ensemble
            model = self.models['voting']
        
        return model.predict(predictions)
    
    def get_model_rankings(self) -> List[Tuple[str, Dict[str, float]]]:
        """Get models ranked by performance"""
        
        rankings = []
        for name, perf in sorted(self.model_performance.items(), 
                               key=lambda x: x[1]['rmse']):
            rankings.append((name, perf))
        
        return rankings

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create example predictions
    example_predictions = [
        [
            PredictionComponent("theme_match", 0.8, 0.9, "Strong theme alignment"),
            PredictionComponent("audio_features", 0.6, 0.7, "Good energy match"),
            PredictionComponent("voter_preference", 0.7, 0.8, "Matches voter taste"),
            PredictionComponent("historical", 0.75, 0.6, "Fits group tendency")
        ],
        [
            PredictionComponent("theme_match", 0.6, 0.8, "Moderate theme fit"),
            PredictionComponent("audio_features", 0.8, 0.9, "Excellent audio match"),
            PredictionComponent("voter_preference", 0.5, 0.6, "Mixed voter appeal"),
            PredictionComponent("historical", 0.65, 0.7, "Reasonable group fit")
        ]
    ]
    
    example_targets = [4.2, 3.1]  # Actual scores
    
    # Test ensemble manager
    manager = EnsembleManager()
    manager.train_all_models(example_predictions, example_targets)
    
    # Make prediction
    test_prediction = manager.predict(example_predictions[0])
    print(f"\nTest prediction: {test_prediction.final_score:.2f} (confidence: {test_prediction.confidence:.2f})")
    print(f"Method: {test_prediction.ensemble_method}")
    print(f"Reasoning: {test_prediction.reasoning}")