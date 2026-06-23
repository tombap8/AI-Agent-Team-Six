import numpy as np
import pandas as pd
from scipy.stats import zscore
import riskfolio as rp
from utils.db_helper import get_engine, get_connection

def col_clean_group(df, cutoff=0.01, asc=False):
    """
    그룹(섹터)별로 아웃라이어를 클램핑한 후, 순위의 Z-Score를 계산합니다.
    """
    res = pd.DataFrame(index=df.index)
    for col in df.columns:
        series = df[col]
        q_low = series.quantile(cutoff)
        q_hi = series.quantile(1 - cutoff)
        trimmed = series.clip(lower=q_low, upper=q_hi)
        
        ranked = trimmed.rank(ascending=asc, na_option='keep')
        
        valid_ranks = ranked.dropna()
        if valid_ranks.empty or len(valid_ranks.unique()) <= 1:
            s_z = pd.Series(0.0, index=df.index)
        else:
            z_vals = zscore(valid_ranks)
            s_z = pd.Series(np.nan, index=df.index)
            s_z.update(pd.Series(z_vals, index=valid_ranks.index))
            
        res[col] = s_z
    return res

def calculate_dynamic_qvm(w_quality=0.33, w_value=0.33, w_momentum=0.34, target_sectors=None, market="KOR"):
    """
    데이터베이스에서 최신 기준일의 다중 팩터 데이터를 조회하여 Z-Score와 QVM 점수를 실시간으로 다시 계산합니다.
    """
    engine = get_engine()
    prefix = "kor" if market == "KOR" else "global"
    
    # 최신 기준일 확인
    try:
        latest_date_df = pd.read_sql(f"SELECT MAX(기준일) as max_date FROM {prefix}_multi_factor", con=engine)
        latest_date = latest_date_df['max_date'].iloc[0]
        if latest_date is None:
            engine.dispose()
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching latest date: {e}")
        engine.dispose()
        return pd.DataFrame()
        
    # 데이터 조회
    query = f"""
        SELECT * FROM {prefix}_multi_factor 
        WHERE 기준일 = '{latest_date}'
    """
    df = pd.read_sql(query, con=engine)
    engine.dispose()
    
    if df.empty:
        return df

    df = df.replace({None: np.nan})
    
    # 1. 퀄리티 Z-score
    q_cols = ['ROE', 'GPA', 'CFO']
    z_q = df.groupby('SEC_NM_KOR', group_keys=False)[q_cols].apply(lambda x: col_clean_group(x, 0.01, False))
    df['z_quality'] = z_q.sum(axis=1, min_count=1)
    
    # 2. 밸류 Z-score
    v_cols_asc = ['PER', 'PBR', 'PCR', 'PSR']
    z_v_asc = df.groupby('SEC_NM_KOR', group_keys=False)[v_cols_asc].apply(lambda x: col_clean_group(x, 0.01, True))
    z_v_desc = df.groupby('SEC_NM_KOR', group_keys=False)[['DY']].apply(lambda x: col_clean_group(x, 0.01, False))
    df['z_value'] = z_v_asc.sum(axis=1, min_count=1) + z_v_desc.sum(axis=1, min_count=1)
    
    # 3. 모멘텀 Z-score
    m_cols = ['12M', 'K_ratio']
    z_m = df.groupby('SEC_NM_KOR', group_keys=False)[m_cols].apply(lambda x: col_clean_group(x, 0.01, False))
    df['z_momentum'] = z_m.sum(axis=1, min_count=1)
    
    # 가중 합산
    df['qvm'] = (w_quality * df['z_quality'].fillna(0) + 
                 w_value * df['z_value'].fillna(0) + 
                 w_momentum * df['z_momentum'].fillna(0))
    
    if target_sectors and len(target_sectors) > 0:
        df = df[df['SEC_NM_KOR'].isin(target_sectors)]
        
    df['rank'] = df['qvm'].rank(ascending=False, method='first')
    df = df.sort_values('rank')
    
    return df

def optimize_portfolio(tickers, method='MaxSharpe', market="KOR"):
    """
    선택한 종목들의 최적 자산배분 비중을 산출합니다.
    """
    if not tickers:
        return {}
        
    engine = get_engine()
    prefix = "kor" if market == "KOR" else "global"
    
    ticker_str = "', '".join(tickers)
    query = f"""
        SELECT 날짜, 종가, 종목코드 FROM {prefix}_price
        WHERE 종목코드 IN ('{ticker_str}')
        ORDER BY 날짜 ASC
    """
    df_price = pd.read_sql(query, con=engine)
    engine.dispose()
    
    if df_price.empty:
        return {t: 1.0 / len(tickers) for t in tickers}
        
    df_pivot = df_price.pivot(index='날짜', columns='종목코드', values='종가').ffill().bfill()
    returns = df_pivot.pct_change().dropna()
    
    if returns.empty or len(returns.columns) < 2:
        return {t: 1.0 / len(tickers) for t in tickers}
        
    try:
        port = rp.Portfolio(returns=returns)
        port.assets_stats(method_mu='hist', method_cov='hist')
        
        model = 'Classic'
        rm = 'MV'
        
        if method == 'MaxSharpe':
            obj = 'Sharpe'
        else:
            obj = 'MinRisk'
            
        w = port.optimization(model=model, rm=rm, obj=obj, rf=0, hist=True)
        return w['weights'].to_dict()
    except Exception as e:
        print(f"Optimization error: {e}, falling back to equal weights")
        return {t: 1.0 / len(tickers) for t in tickers}

def run_backtest(tickers, weights, market="KOR", rebalance_freq="Buy & Hold", fee_ratio=0.0025):
    """
    주기적 리밸런싱 및 거래 비용을 반영하여 백테스트를 실행합니다.
    """
    if not tickers or not weights:
        return pd.DataFrame(), 0, 0, 0, 0
        
    engine = get_engine()
    prefix = "kor" if market == "KOR" else "global"
    
    ticker_str = "', '".join(tickers)
    query_port = f"""
        SELECT 날짜, 종가, 종목코드 FROM {prefix}_price
        WHERE 종목코드 IN ('{ticker_str}')
        ORDER BY 날짜 ASC
    """
    df_port_price = pd.read_sql(query_port, con=engine)
    
    query_bench = f"SELECT 날짜, 종가, 종목코드 FROM {prefix}_price ORDER BY 날짜 ASC"
    df_bench_price = pd.read_sql(query_bench, con=engine)
    engine.dispose()
    
    if df_port_price.empty or df_bench_price.empty:
        return pd.DataFrame(), 0, 0, 0, 0
        
    df_port_pivot = df_port_price.pivot(index='날짜', columns='종목코드', values='종가').ffill().bfill()
    port_rets = df_port_pivot.pct_change().dropna()
    
    df_bench_pivot = df_bench_price.pivot(index='날짜', columns='종목코드', values='종가').ffill().bfill()
    bench_rets = df_bench_pivot.pct_change().dropna()
    bench_daily_ret = bench_rets.mean(axis=1)
    
    common_idx = port_rets.index.intersection(bench_daily_ret.index)
    port_rets = port_rets.loc[common_idx]
    bench_daily_ret = bench_daily_ret.loc[common_idx]
    
    # 가중치 벡터
    target_weights = np.array([weights.get(col, 0) for col in port_rets.columns])
    if target_weights.sum() > 0:
        target_weights = target_weights / target_weights.sum()
    else:
        target_weights = np.ones(len(port_rets.columns)) / len(port_rets.columns)
        
    # 시뮬레이션 루프 (리밸런싱 및 거래 비용 반영)
    portfolio_values = []
    asset_values = target_weights.copy()
    
    for idx, date in enumerate(common_idx):
        daily_ret = port_rets.loc[date].values
        asset_values = asset_values * (1 + daily_ret)
        port_val = asset_values.sum()
        
        # 리밸런싱 조건 (Monthly: 21영업일, Quarterly: 63영업일)
        if rebalance_freq != "Buy & Hold":
            freq_days = 21 if "Monthly" in rebalance_freq else 63
            if idx > 0 and idx % freq_days == 0:
                actual_weights = asset_values / port_val if port_val > 0 else asset_values
                trades = np.abs(actual_weights - target_weights)
                cost = port_val * trades.sum() * fee_ratio
                port_val -= cost
                asset_values = port_val * target_weights
                
        portfolio_values.append(port_val)
        
    # 누적 수익률 계산
    port_cum = np.array(portfolio_values) - 1
    bench_cum = (1 + bench_daily_ret).cumprod() - 1
    
    df_result = pd.DataFrame({
        "Portfolio": port_cum * 100,
        "Benchmark": bench_cum * 100
    }, index=common_idx).reset_index()
    
    days = len(common_idx)
    years = days / 252.0
    
    port_final = port_cum[-1] + 1
    port_cagr = (port_final ** (1 / years) - 1) * 100 if port_final > 0 else 0
    bench_final = bench_cum.iloc[-1] + 1
    bench_cagr = (bench_final ** (1 / years) - 1) * 100 if bench_final > 0 else 0
    
    def calc_mdd(cum_ret_series):
        wealth_index = cum_ret_series + 1
        previous_peaks = np.maximum.accumulate(wealth_index)
        drawdowns = (wealth_index - previous_peaks) / previous_peaks
        return drawdowns.min() * 100
        
    port_mdd = calc_mdd(port_cum)
    bench_mdd = calc_mdd(bench_cum.values)
    
    return df_result, round(port_cagr, 2), round(port_mdd, 2), round(bench_cagr, 2), round(bench_mdd, 2)

def get_technical_indicators(ticker, market="KOR"):
    """
    이동평균선(SMA 20), 볼린저 밴드, 14일 RSI를 계산하고 매수/매도 골든/데드크로스 신호를 생성합니다.
    """
    engine = get_engine()
    prefix = "kor" if market == "KOR" else "global"
    
    query = f"""
        SELECT 날짜, 종가, 시가, 고가, 저가 FROM {prefix}_price
        WHERE 종목코드 = '{ticker}'
        ORDER BY 날짜 ASC
    """
    df = pd.read_sql(query, con=engine)
    engine.dispose()
    
    if df.empty or len(df) < 20:
        return df
        
    # SMA 20
    df['SMA'] = df['종가'].rolling(window=20).mean()
    # Bollinger Bands
    df['std'] = df['종가'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA'] + 2 * df['std']
    df['BB_Lower'] = df['SMA'] - 2 * df['std']
    
    # RSI 14
    delta = df['종가'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Crossover signals
    df['Signal'] = None
    for i in range(1, len(df)):
        close_prev, close_curr = df['종가'].iloc[i-1], df['종가'].iloc[i]
        bbl_prev, bbl_curr = df['BB_Lower'].iloc[i-1], df['BB_Lower'].iloc[i]
        bbu_prev, bbu_curr = df['BB_Upper'].iloc[i-1], df['BB_Upper'].iloc[i]
        
        # Golden Cross (closes crosses above BB Lower)
        if close_prev <= bbl_prev and close_curr > bbl_curr:
            df.at[df.index[i], 'Signal'] = 'BUY'
        # Dead Cross (close crosses below BB Upper)
        elif close_prev >= bbu_prev and close_curr < bbu_curr:
            df.at[df.index[i], 'Signal'] = 'SELL'
            
    return df

def generate_order_signals(tickers, optimized_weights, current_weights=None, capital=10000000, market="KOR"):
    """
    목표 포트폴리오 자산 배분을 바탕으로 현재 보유 대비 매수/매도 주문 수량을 생성합니다.
    """
    if not tickers:
        return pd.DataFrame()
        
    engine = get_engine()
    prefix = "kor" if market == "KOR" else "global"
    
    ticker_str = "', '".join(tickers)
    # Get latest prices and stock names
    query = f"""
        SELECT t.종목코드, t.종목명, t.종가 
        FROM {prefix}_ticker t
        WHERE t.기준일 = (SELECT MAX(기준일) FROM {prefix}_ticker)
          AND t.종목코드 IN ('{ticker_str}')
    """
    df_info = pd.read_sql(query, con=engine)
    engine.dispose()
    
    if df_info.empty:
        return pd.DataFrame()
        
    if current_weights is None:
        current_weights = {t: 0.0 for t in tickers}
        
    orders = []
    for idx, row in df_info.iterrows():
        code = row['종목코드']
        name = row['종목명']
        price = row['종가']
        
        target_w = optimized_weights.get(code, 0.0)
        curr_w = current_weights.get(code, 0.0)
        
        # Calculate target value
        target_value = capital * target_w
        curr_value = capital * curr_w
        diff_value = target_value - curr_value
        
        # Calculate shares (round down or near)
        shares = int(diff_value / price)
        
        if shares > 0:
            action = "매수 (BUY)"
        elif shares < 0:
            action = "매도 (SELL)"
            shares = abs(shares)
        else:
            action = "유지 (HOLD)"
            
        orders.append({
            "종목코드": code,
            "종목명": name,
            "목표 비중": f"{target_w*100:.2f}%",
            "보유 비중": f"{curr_w*100:.2f}%",
            "주문 구분": action,
            "현재가": f"{price:,.2f}" if prefix == "global" else f"{price:,}원",
            "주문 수량": f"{shares}주" if shares > 0 else "-",
            "주문 금액": f"{int(shares*price):,}원" if prefix == "kor" else f"${round(shares*price, 2)}"
        })
        
    return pd.DataFrame(orders)
