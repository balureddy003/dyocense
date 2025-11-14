"""
XGBoost forecasting model

Uses XGBoost for time series forecasting with feature engineering.
Good for data with complex patterns and external regressors.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb

logger = logging.getLogger(__name__)


class XGBoostForecaster:
    """
    XGBoost-based time series forecaster.
    
    Uses lagged features, rolling statistics, and date features
    for prediction.
    """
    
    def __init__(
        self,
        lag_features: list[int] | None = None,
        rolling_windows: list[int] | None = None,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1
    ):
        """
        Initialize XGBoost forecaster.
        
        Args:
            lag_features: Lags to use (e.g., [1, 7, 30] for t-1, t-7, t-30)
            rolling_windows: Rolling window sizes (e.g., [7, 30] for 7-day, 30-day avg)
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate
        """
        self.lag_features = lag_features or [1, 7, 14, 30]
        self.rolling_windows = rolling_windows or [7, 14, 30]
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        
        self.model = None
        self.feature_names = []
        self.logger = logging.getLogger(__name__)
    
    def create_features(
        self,
        data: pd.DataFrame,
        target_col: str = 'y'
    ) -> pd.DataFrame:
        """
        Create time series features.
        
        Args:
            data: DataFrame with datetime index and target column
            target_col: Name of target column
        
        Returns:
            DataFrame with engineered features
        """
        df = data.copy()
        
        # Date features
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['week_of_year'] = df.index.isocalendar().week
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        df['year'] = df.index.year
        
        # Cyclical encoding for day of week (0-6)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Cyclical encoding for month (1-12)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Lag features
        for lag in self.lag_features:
            df[f'lag_{lag}'] = df[target_col].shift(lag)
        
        # Rolling statistics
        for window in self.rolling_windows:
            df[f'rolling_mean_{window}'] = df[target_col].rolling(window=window).mean()
            df[f'rolling_std_{window}'] = df[target_col].rolling(window=window).std()
            df[f'rolling_min_{window}'] = df[target_col].rolling(window=window).min()
            df[f'rolling_max_{window}'] = df[target_col].rolling(window=window).max()
        
        # Difference features
        df['diff_1'] = df[target_col].diff(1)
        df['diff_7'] = df[target_col].diff(7)
        
        # Expanding statistics
        df['expanding_mean'] = df[target_col].expanding().mean()
        df['expanding_std'] = df[target_col].expanding().std()
        
        return df
    
    def fit(
        self,
        data: pd.DataFrame,
        target_col: str = 'y',
        external_features: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Fit XGBoost model to data.
        
        Args:
            data: DataFrame with datetime index and target column
            target_col: Name of target column
            external_features: Additional feature columns to include
        
        Returns:
            Fit results and feature importance
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Data must have DatetimeIndex")
        
        self.logger.info(f"Creating features for {len(data)} observations")
        
        # Create features
        df = self.create_features(data, target_col)
        
        # Drop rows with NaN (from lagging/rolling)
        df = df.dropna()
        
        # Feature columns
        feature_cols = [
            col for col in df.columns
            if col not in [target_col] and not col.startswith('_')
        ]
        
        if external_features:
            feature_cols.extend([col for col in external_features if col in df.columns])
        
        self.feature_names = feature_cols
        
        # Prepare data
        X = df[feature_cols]
        y = df[target_col]
        
        self.logger.info(f"Training XGBoost with {len(feature_cols)} features")
        
        # Train model
        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            objective='reg:squarederror',
            random_state=42
        )
        
        self.model.fit(X, y)
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.logger.info(f"Model trained. Top feature: {importance.iloc[0]['feature']}")
        
        return {
            "status": "success",
            "num_features": len(feature_cols),
            "num_observations": len(X),
            "feature_importance": importance.head(10).to_dict('records')
        }
    
    def predict(
        self,
        data: pd.DataFrame,
        steps: int,
        target_col: str = 'y'
    ) -> dict[str, Any]:
        """
        Generate multi-step forecast.
        
        Uses recursive prediction (predict t+1, add to data, predict t+2, etc.)
        
        Args:
            data: Historical data (used for lag features)
            steps: Number of periods to forecast
            target_col: Name of target column
        
        Returns:
            Forecast results
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        # Create a copy for recursive prediction
        df = data.copy()
        predictions = []
        
        for step in range(steps):
            # Create features for latest data
            df_features = self.create_features(df, target_col)
            
            # Get latest row features
            latest = df_features.iloc[-1:][self.feature_names]
            
            # Predict
            pred = self.model.predict(latest)[0]
            predictions.append(pred)
            
            # Add prediction to dataframe for next iteration
            next_date = df.index[-1] + pd.Timedelta(days=1)
            new_row = pd.DataFrame({target_col: [pred]}, index=[next_date])
            df = pd.concat([df, new_row])
        
        # Create forecast dates
        last_date = data.index[-1]
        forecast_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=steps,
            freq='D'
        )
        
        self.logger.info(f"Generated forecast for {steps} periods")
        
        return {
            "predictions": predictions,
            "dates": forecast_dates.strftime('%Y-%m-%d').tolist()
        }
    
    def predict_with_exogenous(
        self,
        data: pd.DataFrame,
        future_exog: pd.DataFrame,
        target_col: str = 'y'
    ) -> dict[str, Any]:
        """
        Generate forecast with external regressors.
        
        Args:
            data: Historical data
            future_exog: Future values of external features
            target_col: Name of target column
        
        Returns:
            Forecast results
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        # Combine historical and future data
        df = pd.concat([data, future_exog])
        
        # Create features
        df_features = self.create_features(df, target_col)
        
        # Predict for future period
        future_features = df_features.loc[future_exog.index, self.feature_names]
        predictions = self.model.predict(future_features)
        
        return {
            "predictions": predictions.tolist(),
            "dates": future_exog.index.strftime('%Y-%m-%d').tolist()
        }
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> dict[str, Any]:
        """
        Evaluate model on test data.
        
        Args:
            X: Test features
            y: Test target
        
        Returns:
            Accuracy metrics
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        # Predict
        y_pred = self.model.predict(X[self.feature_names])
        
        # Calculate metrics
        mae = np.mean(np.abs(y - y_pred))
        rmse = np.sqrt(np.mean((y - y_pred) ** 2))
        
        # MAPE
        mask = y != 0
        mape = np.mean(np.abs((y[mask] - y_pred[mask]) / y[mask])) * 100 if mask.any() else np.nan
        
        # R²
        r2 = self.model.score(X[self.feature_names], y)
        
        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mape": round(mape, 2) if not np.isnan(mape) else None,
            "r2": round(r2, 4),
            "num_observations": len(y)
        }
    
    def get_feature_importance(self) -> dict[str, Any]:
        """
        Get feature importance from trained model.
        
        Returns:
            Feature importance rankings
        """
        if self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first")
        
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return {
            "feature_importance": importance.to_dict('records'),
            "top_5_features": importance.head(5)['feature'].tolist()
        }
