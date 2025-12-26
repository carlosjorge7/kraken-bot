"""
Enhanced Predictor - Predictor Mejorado con Thresholds, Multi-TF y No-Prediction

Extensión del predictor base que añade:
- PASO 2: Thresholds operativos (LOW/MEDIUM/HIGH)
- PASO 3: Confirmación multi-timeframe
- PASO 4: Reglas de no-predicción
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from predictive.predictor import DirectionalPredictor, PredictionSignal, Direction, Horizon


@dataclass
class NoPredictionInfo:
    """Información sobre por qué no se genera predicción"""
    active: bool
    rules_triggered: List[str]
    note: str


@dataclass
class MultiTimeframeConfirmation:
    """Confirmación multi-timeframe"""
    enabled: bool
    predictions: Dict[str, Dict[str, Any]]  # {timeframe: {direction, confidence}}
    confirmed: bool
    confidence_adjustment: float
    rule: str


@dataclass
class EnhancedPrediction:
    """Predicción mejorada con información adicional"""
    # Campos base
    direction: str
    confidence: float
    horizon: str
    quality: str
    reasons: List[str]
    technical_scores: Dict[str, float]
    timestamp: str
    
    # PASO 3: Multi-timeframe
    confirmation: Optional[MultiTimeframeConfirmation] = None
    
    # PASO 4: No-prediction
    no_prediction: Optional[NoPredictionInfo] = None


class EnhancedPredictor:
    """
    Predictor mejorado que extiende el predictor base.
    
    Añade:
    - Thresholds operativos
    - Confirmación multi-timeframe
    - Reglas de no-predicción
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el predictor mejorado.
        
        Args:
            config: Configuración completa del sistema
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Configuración de predicciones
        pred_config = config.get('predictions', {})
        
        # PASO 2: Thresholds
        self.thresholds = pred_config.get('thresholds', {
            'low': 0.55,
            'medium': 0.65,
            'high': 0.65
        })
        
        # PASO 3: Multi-timeframe
        self.multi_tf_config = pred_config.get('multi_timeframe', {})
        self.multi_tf_enabled = self.multi_tf_config.get('enabled', False)
        
        # PASO 4: No-prediction rules
        self.no_pred_config = pred_config.get('no_prediction', {})
        self.no_pred_enabled = self.no_pred_config.get('enabled', False)
        self.no_pred_rules = self.no_pred_config.get('rules', {})
        
        # Predictor base
        self.base_predictor = DirectionalPredictor(rsi_period=14)
        
        self.logger.info("EnhancedPredictor inicializado")
        if self.multi_tf_enabled:
            self.logger.info("  ✓ Multi-timeframe activado")
        if self.no_pred_enabled:
            self.logger.info("  ✓ Reglas de no-predicción activadas")
    
    def predict(
        self,
        df: pd.DataFrame,
        rsi_series: pd.Series,
        horizon: Horizon = Horizon.NEXT_3_CANDLES,
        symbol: str = None
    ) -> EnhancedPrediction:
        """
        Genera predicción mejorada.
        
        Args:
            df: DataFrame con datos OHLCV
            rsi_series: Serie con RSI calculado
            horizon: Horizonte temporal
            symbol: Símbolo del mercado
        
        Returns:
            EnhancedPrediction con toda la información
        """
        # PASO 4: Verificar reglas de no-predicción PRIMERO
        if self.no_pred_enabled:
            no_pred_info = self._check_no_prediction_rules(df, rsi_series)
            if no_pred_info.active:
                return self._create_no_prediction(horizon, no_pred_info)
        
        # Generar predicción base
        base_signal = self.base_predictor.predict(df, rsi_series, horizon)
        
        # PASO 2: Calcular quality basado en thresholds
        quality = self._calculate_quality(base_signal.confidence)
        
        # Preparar predicción mejorada
        enhanced = EnhancedPrediction(
            direction=base_signal.direction.value,
            confidence=base_signal.confidence,
            horizon=base_signal.horizon.value,
            quality=quality,
            reasons=base_signal.reasons,
            technical_scores=base_signal.technical_scores,
            timestamp=base_signal.timestamp,
            no_prediction=NoPredictionInfo(active=False, rules_triggered=[], note="")
        )
        
        return enhanced
    
    def predict_with_confirmation(
        self,
        predictions_by_tf: Dict[str, PredictionSignal]
    ) -> EnhancedPrediction:
        """
        PASO 3: Genera predicción con confirmación multi-timeframe.
        
        Args:
            predictions_by_tf: {timeframe: PredictionSignal}
        
        Returns:
            EnhancedPrediction con confirmación
        """
        if not self.multi_tf_enabled or len(predictions_by_tf) < 2:
            # Si no está habilitado o no hay suficientes timeframes,
            # retornar la primera predicción sin confirmación
            first_pred = list(predictions_by_tf.values())[0]
            return EnhancedPrediction(
                direction=first_pred.direction.value,
                confidence=first_pred.confidence,
                horizon=first_pred.horizon.value,
                quality=self._calculate_quality(first_pred.confidence),
                reasons=first_pred.reasons,
                technical_scores=first_pred.technical_scores,
                timestamp=first_pred.timestamp,
                no_prediction=NoPredictionInfo(active=False, rules_triggered=[], note="")
            )
        
        # Analizar confirmación
        directions = [p.direction.value for p in predictions_by_tf.values()]
        confidences = [p.confidence for p in predictions_by_tf.values()]
        
        # Verificar si hay consenso (ignoring NEUTRAL)
        non_neutral = [d for d in directions if d != Direction.NEUTRAL.value]
        
        confirmed = False
        adjustment = 0.0
        rule = "NO_CONSENSUS"
        
        if len(non_neutral) >= 2 and len(set(non_neutral)) == 1:
            # Todas las direcciones no-neutrales coinciden
            confirmed = True
            adjustment = self.multi_tf_config.get('confidence_boost', 0.05)
            rule = f"MATCH_DIRECTION_{non_neutral[0]}"
        elif len(set(non_neutral)) > 1:
            # Direcciones contradictorias
            confirmed = False
            adjustment = -self.multi_tf_config.get('confidence_penalty', 0.05)
            rule = "CONTRADICTION"
        else:
            # Una o más es NEUTRAL - señal débil
            confirmed = False
            adjustment = 0.0
            rule = "WEAK_SIGNAL_NEUTRAL"
        
        # Tomar la predicción del primer timeframe como base
        base_tf = list(predictions_by_tf.keys())[0]
        base_pred = predictions_by_tf[base_tf]
        
        # Ajustar confianza
        adjusted_confidence = max(0.0, min(1.0, base_pred.confidence + adjustment))
        
        # Crear confirmación info
        confirmation = MultiTimeframeConfirmation(
            enabled=True,
            predictions={
                tf: {
                    "direction": pred.direction.value,
                    "confidence": pred.confidence
                }
                for tf, pred in predictions_by_tf.items()
            },
            confirmed=confirmed,
            confidence_adjustment=adjustment,
            rule=rule
        )
        
        # Actualizar razones si hay confirmación
        reasons = list(base_pred.reasons)
        if confirmed:
            reasons.insert(0, f"✓ Confirmado por múltiples timeframes ({rule})")
        elif adjustment < 0:
            reasons.append(f"⚠️ Señales contradictorias entre timeframes")
        
        return EnhancedPrediction(
            direction=base_pred.direction.value,
            confidence=adjusted_confidence,
            horizon=base_pred.horizon.value,
            quality=self._calculate_quality(adjusted_confidence),
            reasons=reasons,
            technical_scores=base_pred.technical_scores,
            timestamp=base_pred.timestamp,
            confirmation=confirmation,
            no_prediction=NoPredictionInfo(active=False, rules_triggered=[], note="")
        )
    
    def _calculate_quality(self, confidence: float) -> str:
        """
        PASO 2: Calcula quality basado en thresholds.
        
        Args:
            confidence: Nivel de confianza
        
        Returns:
            'HIGH', 'MEDIUM', o 'LOW'
        """
        if confidence >= self.thresholds['high']:
            return 'HIGH'
        elif confidence >= self.thresholds['low']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _check_no_prediction_rules(
        self,
        df: pd.DataFrame,
        rsi_series: pd.Series
    ) -> NoPredictionInfo:
        """
        PASO 4: Verifica reglas de no-predicción.
        
        Returns:
            NoPredictionInfo indicando si se debe evitar la predicción
        """
        rules_triggered = []
        
        # Regla 1: RSI no disponible
        if rsi_series is None or len(rsi_series) == 0 or pd.isna(rsi_series.iloc[-1]):
            rules_triggered.append("RSI_NOT_AVAILABLE")
        
        # Regla 2: Mercado plano (bajo momentum)
        if len(df) >= 5:
            recent = df.tail(5)
            price_change_pct = abs((recent['close'].iloc[-1] - recent['close'].iloc[0]) / recent['close'].iloc[0])
            
            threshold = self.no_pred_rules.get('low_momentum_threshold', 0.005)
            if price_change_pct < threshold:
                rules_triggered.append("LOW_MOMENTUM")
        
        # Regla 3: Volumen bajo
        if len(df) >= 10:
            recent_vol = df.tail(5)['volume'].mean()
            historical_vol = df['volume'].quantile(self.no_pred_rules.get('low_volume_percentile', 0.20))
            
            if recent_vol < historical_vol:
                rules_triggered.append("LOW_VOLUME")
        
        # Regla 4: Señales contradictorias
        # RSI indica sobrecompra/sobreventa pero precio va en dirección contraria
        if rsi_series is not None and len(rsi_series) > 0 and not pd.isna(rsi_series.iloc[-1]):
            rsi_val = rsi_series.iloc[-1]
            if len(df) >= 3:
                price_momentum = (df['close'].iloc[-1] - df['close'].iloc[-3]) / df['close'].iloc[-3]
                
                # RSI sobreventa pero precio cayendo fuerte
                if rsi_val <= 30 and price_momentum < -0.02:
                    rules_triggered.append("CONTRADICTION_RSI_OVERSOLD_PRICE_DOWN")
                
                # RSI sobrecompra pero precio subiendo fuerte
                elif rsi_val >= 70 and price_momentum > 0.02:
                    rules_triggered.append("CONTRADICTION_RSI_OVERBOUGHT_PRICE_UP")
        
        # Determinar si activar no-prediction
        active = len(rules_triggered) > 0
        
        if active:
            note = f"Sistema evita señal: {', '.join(rules_triggered)}"
        else:
            note = ""
        
        return NoPredictionInfo(
            active=active,
            rules_triggered=rules_triggered,
            note=note
        )
    
    def _create_no_prediction(
        self,
        horizon: Horizon,
        no_pred_info: NoPredictionInfo
    ) -> EnhancedPrediction:
        """
        PASO 4: Crea una predicción NEUTRAL cuando se activa no-prediction.
        
        Args:
            horizon: Horizonte temporal
            no_pred_info: Información de no-predicción
        
        Returns:
            EnhancedPrediction con direction=NEUTRAL y quality=LOW
        """
        # Generar razones legibles
        reason_map = {
            "RSI_NOT_AVAILABLE": "RSI no disponible (datos insuficientes)",
            "LOW_MOMENTUM": "Mercado sin momentum suficiente",
            "LOW_VOLUME": "Volumen por debajo del promedio histórico",
            "CONTRADICTION_RSI_OVERSOLD_PRICE_DOWN": "Señales contradictorias (RSI sobreventa pero precio cayendo)",
            "CONTRADICTION_RSI_OVERBOUGHT_PRICE_UP": "Señales contradictorias (RSI sobrecompra pero precio subiendo)"
        }
        
        reasons = [
            f"No prediction: {reason_map.get(rule, rule)}"
            for rule in no_pred_info.rules_triggered
        ]
        
        if not reasons:
            reasons = ["No prediction: condiciones no favorables"]
        
        return EnhancedPrediction(
            direction=Direction.NEUTRAL.value,
            confidence=0.50,  # Confianza neutral
            horizon=horizon.value,
            quality='LOW',
            reasons=reasons,
            technical_scores={},
            timestamp=datetime.now().isoformat(),
            no_prediction=no_pred_info
        )
