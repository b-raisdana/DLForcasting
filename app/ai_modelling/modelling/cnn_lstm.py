import argparse
import sys
from datetime import timedelta, datetime
from random import shuffle

import pandas as pd
import tensorflow as tf

from app.Config import app_config
from app.ai_modelling.cnn_lstm_mt_indicators_to_profit_loss.model import train_model
from app.ai_modelling.cnn_lstm_mt_indicators_to_profit_loss.trining_datasets import plot_train_data_of_mt_n_profit, \
    train_data_of_mt_n_profit
from app.data_processing.ohlcv import read_multi_timeframe_ohlcv
from app.helper.helper import date_range, log_d, date_range_to_string

print('tensorflow:' + tf.__version__)

cnn_lstd_model_x_lengths = {
    'structure': (128, 5),
    'pattern': (256, 5),
    'trigger': (256, 5),
    'double': (256, 5),
}


def ceil_start_of_slide(t_date: datetime, slide: timedelta):
    if (t_date - datetime(t_date.year, t_date.month, t_date.day, tzinfo=t_date.tzinfo)) > timedelta(0):
        t_date = datetime(t_date.year, t_date.month, t_date.day + 1, tzinfo=t_date.tzinfo)
    days = (t_date - datetime(t_date.year, 1, 1, tzinfo=t_date.tzinfo)).days
    rounded_days = (days // slide.days) * slide.days + (slide.days if days % slide.days > 0 else 0)
    return datetime(t_date.year, 1, 1, tzinfo=t_date.tzinfo) + rounded_days * timedelta(days=1)


def overlapped_quarters(i_date_range, length=timedelta(days=30 * 3), slide=timedelta(days=30 * 1.5)):
    if i_date_range is None:
        i_date_range = app_config.processing_date_range
    start, end = date_range(i_date_range)
    rounded_start = ceil_start_of_slide(start, slide)
    list_of_periods = [(p_start, p_start + length) for p_start in
                       pd.date_range(rounded_start, end - length, freq=slide)]
    return list_of_periods


''' todo:
- scale profits
- make sure about scale of signal
    + if no drawdown
        + signal shall be number of ATRs
    + in case of drawdown
        + be number of ATRs 
+ add OBV MACD
+ add CCI
+ add RSI
+ add fibo BB + max hit
+ add MFI
+ Add Ichimoku
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for processing OHLCV data.")
    # parser.add_argument("--do_not_fetch_prices", action="store_true", default=False,
    #                     help="Flag to indicate if prices should not be fetched (default: False).")
    args = parser.parse_args()
    print("Python:" + sys.version)

    # Apply config from arguments
    app_config.processing_date_range = "22-08-15.00-00T24-10-30.00-00"
    # config.do_not_fetch_prices = args.do_not_fetch_prices
    # seed(42)
    # np.random.seed(42)

    while True:
        quarters = overlapped_quarters(app_config.processing_date_range)
        shuffle(quarters)
        for start, end in quarters:
            log_d(f'quarter start:{start} end:{end}##########################################')
            app_config.processing_date_range = date_range_to_string(start=start, end=end)
            for symbol in [
                'BTCUSDT',
                # # 'ETHUSDT',
                'BNBUSDT',
                'EOSUSDT',
                # 'TRXUSDT',
                'TONUSDT',
                # 'SOLUSDT',
            ]:
                # try:
                log_d(f'Symbol:{symbol}##########################################')
                app_config.under_process_symbol = symbol
                # n_mt_ohlcv = read_multi_timeframe_rolling_mean_std_ohlcv(config.processing_date_range)
                mt_ohlcv = read_multi_timeframe_ohlcv(app_config.processing_date_range)
                # base_ohlcv = single_timeframe(mt_ohlcv, '15min')
                batch_size = 128
                Xs, ys, X_dfs, y_dfs, y_timeframe, y_tester_dfs = (
                    train_data_of_mt_n_profit('4h', mt_ohlcv, cnn_lstd_model_x_lengths, batch_size))
                for i in range(0, batch_size, int(batch_size / 1)):
                    plot_train_data_of_mt_n_profit(X_dfs, y_dfs, y_tester_dfs, i)
                nop = 1
                t_model = train_model(Xs, ys, cnn_lstd_model_x_lengths, batch_size)
                # except Exception as e:
                #     log_e(e)
"""
Potential Areas of Improvement for Professional Price Forecasting:

    Excessive Use of CNN Layers:
        While CNNs can capture local patterns in time-series data, the use of multiple convolutional layers might not be necessary for financial time-series forecasting. Generally, financial time-series models rely more heavily on recurrent structures like LSTMs or GRUs, rather than deep CNN architectures.
        You might consider reducing the number of CNN layers or simplifying the network to focus more on temporal dependencies.

    More Complex LSTM or GRU Structures:
        Instead of a single LSTM layer, you could consider stacking multiple LSTM layers or using GRU (Gated Recurrent Units), which is a simpler alternative but can sometimes perform better in price forecasting tasks.
        You could also experiment with Bidirectional LSTMs or Attention Mechanisms to give the model more flexibility in capturing dependencies both forward and backward in time.

    Incorporating External Features:
        Financial markets are often influenced by factors beyond just historical prices, such as trading volume, economic indicators, sentiment data, and news. You might want to integrate external features (such as trading volume, market sentiment, or macroeconomic variables) into your model.
        This could be done via multi-input models where different features (price, volume, sentiment) are processed separately and combined before the final prediction layer.

    Model Interpretability:
        For professional models, interpretability is important. You may want to ensure that the model's decisions are explainable, especially when dealing with financial data.
        Consider techniques like SHAP (Shapley Additive Explanations) or LIME (Local Interpretable Model-agnostic Explanations) for model interpretability, which can help you understand the decision-making process of your model.

    Advanced Time-Series Models:
        While CNN-LSTM models can perform well, there are also models like Transformer-based architectures (e.g., Temporal Fusion Transformers) or even ARIMA (AutoRegressive Integrated Moving Average) models that are tailored specifically for time-series forecasting tasks.
        XGBoost and LightGBM models have also been shown to perform well in certain forecasting scenarios, where you can create lagged features and use tree-based models.

Stacked LSTM Layers:

    You could experiment with a stacked LSTM, which would allow the model to capture more complex patterns over time.


lstm_1 = LSTM(lstm_units, return_sequences=True, name=f'{model_prefix}_lstm_1')(tf.expand_dims(flatten, axis=1))
lstm_2 = LSTM(lstm_units, return_sequences=False, name=f'{model_prefix}_lstm_2')(lstm_1)

Attention Mechanism:

    Adding an attention mechanism might help the model focus on more important time steps when making predictions. This is especially useful when the model is trying to predicting prices based on historical data with varying importance at different points in time.

Incorporate Financial Indicators:

    If you are working with stock or cryptocurrency prices, consider adding technical indicators like RSI, MACD, or Bollinger Bands as additional features. These indicators capture market trends and could improve the model's predictive power.

Experiment with More Complex Architectures:

    You could also experiment with Transformer-based models such as the Temporal Fusion Transformer (TFT), which have shown significant promise in time-series forecasting tasks, especially in financial data.

Hyperparameter Tuning:

    Use Grid Search or Random Search to fine-tune hyperparameters like filters, lstm_units, dropout_rate, and the number of CNN layers. This ensures the model is not underfitting or overfitting.
"""
