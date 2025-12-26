"""
Directional Predictor - Predictor de Dirección Basado en Reglas

Sistema de predicción probabilística que analiza indicadores técnicos
para predecir la dirección más probable del precio (UP/DOWN).

NO usa Machine Learning. Solo reglas técnicas explicables.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class Direction(str, Enum):
    """Direcciones posibles de la predicción"""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


class Horizon(str, Enum):
    """Horizontes temporales para la predicción"""
    NEXT_1_CANDLE = "next_1_candle"
    NEXT_3_CANDLES = "next_3_candles"
    NEXT_5_CANDLES = "next_5_candles"


@dataclass
class PredictionSignal:
    """
    Señal de predicción con toda la información relevante.
    
    Attributes:
        direction: Dirección predicha (UP/DOWN/NEUTRAL)
        confidence: Nivel de confianza (0.0 - 1.0)
        horizon: Horizonte temporal de la predicción
        reasons: Lista de razones que justifican la predicción
        technical_scores: Scores individuales de cada indicador
        timestamp: Momento de la predicción
    """
    direction: Direction
    confidence: float
    horizon: Horizon
    reasons: List[str]
    technical_scores: Dict[str, float]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        
        # Validar confianza
        self.confidence = max(0.0, min(1.0, self.confidence))


class DirectionalPredictor:
    """
    Predictor de dirección basado en reglas técnicas.
    
    Analiza múltiples señales técnicas y las combina para generar
    una predicción probabilística de dirección.
    
    NO predice precio exacto, solo dirección probable.
    """
    
    # Umbrales de confianza
    MIN_CONFIDENCE_THRESHOLD = 0.5  # Mínimo para considerar señal válida
    HIGH_CONFIDENCE_THRESHOLD = 0.7  # Alta confianza
    
    # Pesos para cada señal técnica (deben sumar 1.0)
    WEIGHTS = {
        'rsi_signal': 0.35,      # RSI es muy confiable
        'rsi_momentum': 0.20,    # Momentum del RSI
        'price_momentum': 0.25,  # Momentum del precio
        'volume_trend': 0.20,    # Tendencia del volumen
    }
    
    def __init__(self, rsi_period: int = 14):
        """
        Inicializa el predictor.
        
        Args:
            rsi_period: Periodo para cálculo de RSI
        """
        self.logger = logging.getLogger(__name__)
        self.rsi_period = rsi_period
    
    def predict(
        self,
        df: pd.DataFrame,
        rsi_series: pd.Series,
        horizon: Horizon = Horizon.NEXT_3_CANDLES
    ) -> PredictionSignal:
        """
        Genera una predicción de dirección basada en el análisis técnico.
        
        Args:
            df: DataFrame con datos OHLCV
            rsi_series: Serie con valores RSI calculados
            horizon: Horizonte temporal de la predicción
        
        Returns:
            PredictionSignal con la predicción completa
        """
        if df.empty or len(df) < 10:
            return self._neutral_signal(horizon, "Datos insuficientes")
        
        # Calcular scores individuales
        scores = self._calculate_technical_scores(df, rsi_series)
        
        # Combinar scores con pesos
        weighted_score = self._combine_scores(scores)
        
        # Determinar dirección y confianza
        direction, confidence = self._score_to_prediction(weighted_score)
        
        # Generar razones explicativas
        reasons = self._generate_reasons(df, rsi_series, scores, direction)
        
        return PredictionSignal(
            direction=direction,
            confidence=confidence,
            horizon=horizon,
            reasons=reasons,
            technical_scores=scores
        )
    
    def _calculate_technical_scores(
        self,
        df: pd.DataFrame,
        rsi_series: pd.Series
    ) -> Dict[str, float]:
        """
        Calcula scores individuales para cada señal técnica.
        
        Returns:
            Dict con scores normalizados entre -1.0 (bajista) y +1.0 (alcista)
        """
        scores = {}
        
        # 1. RSI Signal Score
        scores['rsi_signal'] = self._score_rsi_signal(rsi_series)
        
        # 2. RSI Momentum Score
        scores['rsi_momentum'] = self._score_rsi_momentum(rsi_series)
        
        # 3. Price Momentum Score
        scores['price_momentum'] = self._score_price_momentum(df)
        
        # 4. Volume Trend Score
        scores['volume_trend'] = self._score_volume_trend(df)
        
        return scores
    
    def _score_rsi_signal(self, rsi_series: pd.Series) -> float:
        """
        Score basado en el valor actual del RSI.
        
        Lógica:
        - RSI < 30: Sobreventa → Probable rebote UP (+0.8 a +1.0)
        - RSI > 70: Sobrecompra → Probable corrección DOWN (-0.8 a -1.0)
        - RSI 40-60: Neutral (0.0)
        - RSI 30-40: Moderadamente alcista (+0.3 a +0.5)
        - RSI 60-70: Moderadamente bajista (-0.3 a -0.5)
        
        Returns:
            float: Score entre -1.0 y +1.0
        """
        if len(rsi_series) < 2 or pd.isna(rsi_series.iloc[-1]):
            return 0.0
        
        rsi = rsi_series.iloc[-1]
        
        # Sobreventa extrema → Muy alcista
        if rsi <= 20:
            return 1.0
        elif rsi <= 30:
            return 0.5 + (30 - rsi) / 20  # 0.5 a 1.0
        
        # Sobrecompra extrema → Muy bajista
        elif rsi >= 80:
            return -1.0
        elif rsi >= 70:
            return -0.5 - (rsi - 70) / 20  # -0.5 a -1.0
        
        # Zona neutral con sesgo
        elif rsi < 40:
            # Entre 30 y 40 → Moderadamente alcista
            return (40 - rsi) / 20  # 0.0 a 0.5
        elif rsi > 60:
            # Entre 60 y 70 → Moderadamente bajista
            return -(rsi - 60) / 20  # 0.0 a -0.5
        else:
            # Zona neutral (40-60)
            return 0.0
    
    def _score_rsi_momentum(self, rsi_series: pd.Series) -> float:
        """
        Score basado en la tendencia/momentum del RSI.
        
        Analiza si el RSI está subiendo o bajando (cambio reciente).
        
        Returns:
            float: Score entre -1.0 y +1.0
        """
        if len(rsi_series) < 5:
            return 0.0
        
        # Usar últimas 3 velas para detectar tendencia
        recent_rsi = rsi_series.iloc[-3:].dropna()
        
        if len(recent_rsi) < 2:
            return 0.0
        
        # Calcular pendiente simple
        rsi_change = recent_rsi.iloc[-1] - recent_rsi.iloc[0]
        
        # Normalizar: cambios típicos son de -10 a +10 en 3 velas
        # Pendiente positiva → alcista, negativa → bajista
        normalized_slope = np.tanh(rsi_change / 10)  # Suaviza con tanh
        
        return float(normalized_slope)
    
    def _score_price_momentum(self, df: pd.DataFrame) -> float:
        """
        Score basado en el momentum del precio.
        
        Analiza:
        - Cambio de precio reciente (últimas 3-5 velas)
        - Posición del cierre vs apertura en última vela
        
        Returns:
            float: Score entre -1.0 y +1.0
        """
        if len(df) < 5:
            return 0.0
        
        recent = df.tail(5)
        
        # 1. Cambio de precio en las últimas velas
        price_change_pct = (recent['close'].iloc[-1] - recent['close'].iloc[0]) / recent['close'].iloc[0]
        
        # 2. Posición del cierre en la última vela
        last_candle = recent.iloc[-1]
        candle_range = last_candle['high'] - last_candle['low']
        
        if candle_range > 0:
            # Posición del cierre en el rango (0 = low, 1 = high)
            close_position = (last_candle['close'] - last_candle['low']) / candle_range
            close_score = (close_position - 0.5) * 2  # -1 a +1
        else:
            close_score = 0.0
        
        # Combinar ambos factores
        momentum_score = np.tanh(price_change_pct * 100) * 0.7  # Peso mayor
        candle_score = close_score * 0.3  # Peso menor
        
        return float(momentum_score + candle_score)
    
    def _score_volume_trend(self, df: pd.DataFrame) -> float:
        """
        Score basado en la tendencia del volumen.
        
        Lógica:
        - Volumen creciente con precio subiendo → Confirmación alcista
        - Volumen creciente con precio bajando → Confirmación bajista
        - Volumen bajo → Señal débil (cerca de 0)
        
        Returns:
            float: Score entre -1.0 y +1.0
        """
        if len(df) < 10:
            return 0.0
        
        recent = df.tail(5)
        older = df.tail(10).head(5)
        
        # Comparar volumen promedio reciente vs anterior
        recent_vol = recent['volume'].mean()
        older_vol = older['volume'].mean()
        
        if older_vol == 0:
            return 0.0
        
        vol_change = (recent_vol - older_vol) / older_vol
        
        # Dirección del precio reciente
        price_direction = 1 if recent['close'].iloc[-1] > recent['close'].iloc[0] else -1
        
        # Si volumen sube Y precio sube → Alcista
        # Si volumen sube Y precio baja → Bajista
        # Si volumen baja → Señal débil
        
        if vol_change > 0.2:  # Volumen aumentó significativamente
            return float(price_direction * 0.7)
        elif vol_change < -0.2:  # Volumen cayó
            return 0.0  # Señal débil
        else:
            return float(price_direction * 0.3)
    
    def _combine_scores(self, scores: Dict[str, float]) -> float:
        """
        Combina scores individuales usando pesos definidos.
        
        Returns:
            float: Score combinado entre -1.0 y +1.0
        """
        weighted_sum = sum(
            scores.get(key, 0.0) * weight
            for key, weight in self.WEIGHTS.items()
        )
        
        return weighted_sum
    
    def _score_to_prediction(self, score: float) -> Tuple[Direction, float]:
        """
        Convierte score combinado a dirección y confianza.
        
        Score interpretation:
        - > +0.3: UP con confianza proporcional
        - < -0.3: DOWN con confianza proporcional
        - -0.3 a +0.3: NEUTRAL
        
        Returns:
            Tuple[Direction, confidence]
        """
        # Determinar dirección
        if score > 0.3:
            direction = Direction.UP
            # Confianza: mapear score [0.3, 1.0] a [0.5, 1.0]
            confidence = 0.5 + (score - 0.3) / 1.4
        elif score < -0.3:
            direction = Direction.DOWN
            # Confianza: mapear score [-1.0, -0.3] a [0.5, 1.0]
            confidence = 0.5 + (-score - 0.3) / 1.4
        else:
            direction = Direction.NEUTRAL
            # Confianza baja en zona neutral
            confidence = 0.3 + abs(score) / 3
        
        # Asegurar que confianza esté en rango válido
        confidence = max(0.0, min(1.0, confidence))
        
        return direction, confidence
    
    def _generate_reasons(
        self,
        df: pd.DataFrame,
        rsi_series: pd.Series,
        scores: Dict[str, float],
        direction: Direction
    ) -> List[str]:
        """
        Genera lista de razones explicativas para la predicción.
        
        Returns:
            List[str]: Razones en lenguaje natural
        """
        reasons = []
        
        if direction == Direction.NEUTRAL:
            reasons.append("Señales técnicas mixtas o débiles")
            return reasons
        
        # Analizar cada componente y agregar razones relevantes
        
        # 1. RSI Signal
        rsi_score = scores.get('rsi_signal', 0.0)
        if abs(rsi_score) > 0.5:
            if len(rsi_series) > 0 and pd.notna(rsi_series.iloc[-1]):
                rsi_val = rsi_series.iloc[-1]
                if rsi_val <= 30:
                    reasons.append(f"RSI en sobreventa ({rsi_val:.1f}) - probable rebote")
                elif rsi_val >= 70:
                    reasons.append(f"RSI en sobrecompra ({rsi_val:.1f}) - probable corrección")
                elif direction == Direction.UP and rsi_val < 50:
                    reasons.append(f"RSI bajo ({rsi_val:.1f}) con espacio para subir")
                elif direction == Direction.DOWN and rsi_val > 50:
                    reasons.append(f"RSI alto ({rsi_val:.1f}) con riesgo de caída")
        
        # 2. RSI Momentum
        rsi_momentum_score = scores.get('rsi_momentum', 0.0)
        if abs(rsi_momentum_score) > 0.3:
            if rsi_momentum_score > 0:
                reasons.append("RSI con tendencia alcista")
            else:
                reasons.append("RSI con tendencia bajista")
        
        # 3. Price Momentum
        price_score = scores.get('price_momentum', 0.0)
        if abs(price_score) > 0.4:
            if len(df) >= 5:
                recent_change = ((df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]) * 100
                if price_score > 0:
                    reasons.append(f"Momentum de precio positivo ({recent_change:+.2f}%)")
                else:
                    reasons.append(f"Momentum de precio negativo ({recent_change:+.2f}%)")
        
        # 4. Volume Trend
        vol_score = scores.get('volume_trend', 0.0)
        if abs(vol_score) > 0.4:
            if len(df) >= 10:
                recent_vol = df.tail(5)['volume'].mean()
                older_vol = df.tail(10).head(5)['volume'].mean()
                vol_change_pct = ((recent_vol - older_vol) / older_vol) * 100 if older_vol > 0 else 0
                
                if vol_score > 0:
                    reasons.append(f"Volumen creciente confirmando tendencia ({vol_change_pct:+.1f}%)")
                elif vol_score < -0.3:
                    reasons.append("Volumen decreciente - señal débil")
        
        # Si no hay razones específicas, agregar una genérica
        if not reasons:
            if direction == Direction.UP:
                reasons.append("Indicadores técnicos sugieren presión alcista")
            else:
                reasons.append("Indicadores técnicos sugieren presión bajista")
        
        return reasons
    
    def _neutral_signal(self, horizon: Horizon, reason: str) -> PredictionSignal:
        """
        Crea una señal neutral cuando no hay datos suficientes.
        
        Returns:
            PredictionSignal neutral
        """
        return PredictionSignal(
            direction=Direction.NEUTRAL,
            confidence=0.0,
            horizon=horizon,
            reasons=[reason],
            technical_scores={}
        )
    
    def get_prediction_quality(self, signal: PredictionSignal) -> str:
        """
        Evalúa la calidad de una predicción.
        
        Returns:
            str: 'HIGH', 'MEDIUM', 'LOW'
        """
        if signal.direction == Direction.NEUTRAL:
            return 'LOW'
        
        if signal.confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return 'HIGH'
        elif signal.confidence >= self.MIN_CONFIDENCE_THRESHOLD:
            return 'MEDIUM'
        else:
            return 'LOW'
