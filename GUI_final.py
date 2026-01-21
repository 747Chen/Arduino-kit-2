# 口令：streamlit run GUI_final.py
# 接线指南：
# 16bit接IIC， 电流传感器接16bit的A1蓝色接口
# LED指示灯接D5绿色和黑色口， relay接D7
# 温度传感器接A3口
# 传入数据格式：Temp: 0.00 °C | Irms: 0.00000

# 在原有导入基础上添加
import pytz
import numpy as np
from datetime import datetime, timedelta
import requests

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import time
import serial
import queue
import regex as re

from functools import lru_cache
import json
from pathlib import Path

PRICE_CACHE_DIR = Path("./price_cache")
PRICE_CACHE_DIR.mkdir(exist_ok=True)

# 页面配置
st.set_page_config(
    page_title="ESP32 Temperature Monitoring System",
    page_icon="",
    layout="wide"
)

# 自定义样式
st.markdown("""
<style>
    /* 主标题 */
    .main-header {
        text-align: center;
        color: #1E88E5;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }

    /* 温度卡片 */
    .temp-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 25px;
        color: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }

    .temp-card:hover {
        transform: translateY(-5px);
    }

    /* 电流卡片 */
    .current-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 15px;
        padding: 25px;
        color: white;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* 状态指示灯 */
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }

    .connected {
        background-color: #00E676;
    }

    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    /* 数据表格行样式 */
    .temp-high {
        background-color: rgba(255, 82, 82, 0.1) !important;
        font-weight: bold;
    }

    .temp-normal {
        background-color: rgba(76, 175, 80, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'temperature_data' not in st.session_state:
    st.session_state.temperature_data = []
    st.session_state.current_data = []
    st.session_state.timestamps = []
    st.session_state.last_update = datetime.now()
    st.session_state.data_queue = queue.Queue()
    st.session_state.serial_connected = False
    st.session_state.current_mode = "WAITING"  # 新增：保存当前模式
    st.session_state.serial_conn = None  # 新增：保存串口连接

# 标题
st.markdown('<h1 class="main-header">ESP32 Temperature Monitoring System</h1>', unsafe_allow_html=True)

# 侧边栏 - 设置面板
with st.sidebar:
    st.markdown("### System Settings")

    # 串口设置
    st.markdown("#### Serial Connection")
    com_port = st.selectbox("COM Port", ["COM3", "COM4", "COM5", "/dev/ttyUSB0", "/dev/ttyACM0"])
    baud_rate = st.selectbox("Baud Rate", [9600, 115200, 57600, 38400], index=1)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Connect ESP32", type="primary", use_container_width=True):
            try:
                if st.session_state.serial_conn and st.session_state.serial_conn.is_open:
                    st.session_state.serial_conn.close()
                st.session_state.serial_conn = serial.Serial(com_port, baud_rate, timeout=1)
                time.sleep(2)  # 等待初始化
                st.session_state.serial_connected = True
                st.success(f"Connected to {com_port} at {baud_rate} baud")
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")
                st.session_state.serial_connected = False

    with col2:
        if st.button("Disconnect", use_container_width=True):
            if st.session_state.serial_conn and st.session_state.serial_conn.is_open:
                st.session_state.serial_conn.close()
            st.session_state.serial_connected = False
            st.warning("Disconnected")

    st.markdown("---")

    # 显示设置
    st.markdown("#### Display Settings")
    chart_theme = st.selectbox(
        "Chart Theme",
        ["plotly_white", "plotly_dark", "seaborn", "ggplot2", "simple_white"]
    )

    data_points = st.slider("Number of Data Points to Display", 50, 500, 200)

    # 温度阈值设置
    st.markdown("#### Temperature Thresholds")
    temp_warning = st.slider("Warning Threshold (°C)", 20, 50, 30)
    temp_danger = st.slider("Danger Threshold (°C)", 25, 60, 35)

    st.markdown("---")

    # 系统信息
    st.markdown("#### System Status")
    st.markdown(f"""
    <div style="background-color: #396453; padding: 10px; border-radius: 5px;">
        <span class="status-dot connected"></span> Data Update: every 2s<br>
        <span class="status-dot connected"></span> Sensor Update: every 5s<br>
        <span class="status-dot connected"></span> Data Points: {len(st.session_state.temperature_data)}<br>
        <span class="status-dot connected"></span> Last Update: {st.session_state.last_update.strftime('%H:%M:%S')}<br>
        <span class="status-dot connected"></span> Mode: {st.session_state.current_mode}
    </div>
    """, unsafe_allow_html=True)


# 模拟ESP32数据读取（在实际使用中替换为真正的串口读取）
def read_from_esp32_simulation():
    """模拟从ESP32读取数据"""
    try:
        base_temp = 0
        temp = 1
        current = 1

        # 模拟模式切换
        current_time = time.time()
        mode = "AUTO" if int(current_time) % 10 < 5 else "MANUAL"

        return {
            "temperature": round(temp, 2),
            "current": round(current, 2),
            "mode": mode,
            "timestamp": datetime.now(),
            "source": "simulation"
        }
    except Exception as e:
        print(f"Simulation Error: {e}")
        return None

# 真正的ESP32数据读取函数
def read_from_esp32_serial():
    """
    从ESP32串口读取真实数据
    解析格式:  Temp: 8.86 °C | Irms: 0.00000
    """
    try:
        if not st.session_state.serial_conn or not st.session_state.serial_conn.is_open:
            return None

        ser = st.session_state.serial_conn

        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            if not line:
                return None

            # 新增：过滤掉不需要的行
            # 忽略纯数字行（如"1"）和处理消息的标识行
            if (line.isdigit() or
                    "handleNewMessages" in line or
                    "/state" in line or
                    len(line) < 5):  # 忽略过短的行
                print(f"Ignoring line: {line}")  # 调试信息
                return None

            # 使用正则提取所有数字，包括浮点数
            numbers = re.findall(r"[-+]?\d*\.\d+|[-+]?\d+", line)

            # 检测模式
            current_mode = "UNKNOWN"
            if "AUTO" in line.upper():
                current_mode = "AUTO"
            elif "MANUAL" in line.upper():
                current_mode = "MANUAL"

            if len(numbers) >= 2:
                temp_val = float(numbers[0])
                irms_val = float(numbers[1])

                return {
                    "temperature": temp_val,
                    "current": irms_val,
                    "mode": current_mode,
                    "timestamp": datetime.now(),
                    "source": "serial"
                }
            elif len(numbers) >= 1:
                # 如果只有一个数字，检查是否是温度格式
                temp_val = float(numbers[0])

                # 额外检查：确保这真的是温度数据（检查是否有"Temp"或"°C"标识）
                if "Temp" in line or "°C" in line:
                    # 验证温度值是否合理
                    if temp_val >= -40 and temp_val <= 100:
                        return {
                            "temperature": temp_val,
                            "current": 0.0,
                            "mode": current_mode,
                            "timestamp": datetime.now(),
                            "source": "serial"
                        }
                else:
                    return None

        return None

    except Exception as e:
        print(f"Serial Read Error: {e}")
        return None


# 电价获取和计算相关函数
def get_ree_price(start_date=None, end_date=None, include_pvpc=False):
    """
    从REE API获取西班牙电价数据
    """
    # API配置
    endpoint = 'https://apidatos.ree.es'
    get_archives = '/en/datos/mercados/precios-mercados-tiempo-real'

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Host': 'apidatos.ree.es'
    }

    # 设置默认时间范围
    if start_date is None:
        spain_tz = pytz.timezone('Europe/Madrid')
        start_date = datetime.now(spain_tz)

    if end_date is None:
        end_date = start_date + timedelta(hours=24)

    # 格式化时间字符串
    start_date_str = start_date.strftime('%Y-%m-%dT%H:%M')
    end_date_str = end_date.strftime('%Y-%m-%dT%H:%M')

    params = {
        'start_date': start_date_str,
        'end_date': end_date_str,
        'time_trunc': 'hour'
    }

    try:
        # 发送API请求
        response = requests.get(
            endpoint + get_archives,
            headers=headers,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        # 解析JSON数据
        data_json = response.json()

        # 验证数据结构
        if 'included' not in data_json or len(data_json['included']) < 2:
            raise ValueError("ERROR: Data structure cannot be read")

        # 提取现货市场价格
        spot_market_data = None
        pvpc_data = None

        for item in data_json['included']:
            item_type = item.get('type', '')
            if item_type == 'Precio mercado spot (€/MWh)':
                spot_market_data = item
            elif item_type == 'PVPC (€/MWh)':
                pvpc_data = item

        if spot_market_data is None:
            raise ValueError("ERROR: No market data found")

        # 提取数据
        spot_values = spot_market_data['attributes']['values']

        # 构建数据列表
        data_records = []

        for data_point in spot_values:
            record = {
                'datetime': datetime.fromisoformat(data_point['datetime'].replace('Z', '+00:00')),
                'spot_price': data_point['value'],  # €/MWh
                'spot_price_eur_kwh': data_point['value'] / 1000  # 转换为€/kWh
            }

            data_records.append(record)

        # 创建DataFrame
        df = pd.DataFrame(data_records)
        df = df.sort_values('datetime')
        df = df.reset_index(drop=True)

        return df

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network connection error: {e}")
        return pd.DataFrame()

    except ValueError as e:
        print(f"ERROR: structure error: {e}")
        return pd.DataFrame()

    except Exception as e:
        print(f"ERROR: Unknown error: {e}")
        return pd.DataFrame()


def get_ree_price_with_fallback(start_date=None, end_date=None):
    """
    获取电价数据，如果API失败则返回恒定电价0.15€/MWh
    """
    try:
        # 尝试从缓存读取
        cache_file = PRICE_CACHE_DIR / f"price_{datetime.now().strftime('%Y%m%d')}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                # 检查缓存是否过期（超过30分钟）
                cache_time = datetime.fromisoformat(cached_data['timestamp'])
                if (datetime.now() - cache_time).seconds < 1800:
                    # 从缓存恢复数据
                    records = []
                    for record in cached_data['data']:
                        # 确保datetime是datetime对象
                        dt = datetime.fromisoformat(record['datetime'])
                        records.append({
                            'datetime': dt,
                            'spot_price': record['spot_price'],
                            'spot_price_eur_kwh': record['spot_price'] / 1000
                        })
                    df = pd.DataFrame(records)
                    print(f"Using cached price data from {cache_time}")
                    return df

        # 从API获取数据
        api_df = get_ree_price(start_date, end_date)

        if not api_df.empty:
            # 缓存数据
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': []
            }
            for _, row in api_df.iterrows():
                cache_data['data'].append({
                    'datetime': row['datetime'].isoformat(),
                    'spot_price': row['spot_price']
                })

            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)

            return api_df
        else:
            # API返回空数据，使用后备方案
            raise ValueError("API returned empty data")

    except Exception as e:
        print(f"电价API获取失败，使用后备方案: {e}")
        return generate_fallback_price_data(start_date, end_date)


def generate_fallback_price_data(start_date=None, end_date=None):
    """
    生成后备电价数据：恒定0.15€/MWh (0.00015€/kWh)
    """
    spain_tz = pytz.timezone('Europe/Madrid')

    if start_date is None:
        start_date = datetime.now(spain_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    if end_date is None:
        end_date = start_date + timedelta(hours=24)

    # 生成24小时数据
    data_records = []
    current = start_date

    while current < end_date:
        record = {
            'datetime': current,
            'spot_price': 0.15,  # €/MWh
            'spot_price_eur_kwh': 0.15 / 1000  # €/kWh
        }
        data_records.append(record)
        current += timedelta(hours=1)

    df = pd.DataFrame(data_records)
    print("Using fallback price data: 0.15€/MWh")
    return df


def get_current_hour_price():
    """
    获取当前小时的电价（使用后备方案）
    """
    try:
        spain_tz = pytz.timezone('Europe/Madrid')
        now = datetime.now(spain_tz)

        # 获取今日电价数据（使用带后备的函数）
        today_prices = get_ree_price_with_fallback()

        if not today_prices.empty:
            # 找到当前小时的电价
            current_hour = now.replace(minute=0, second=0, microsecond=0)

            # 将电价数据时间转换为西班牙时区
            for idx, row in today_prices.iterrows():
                # 确保price_time是datetime对象
                price_time = row['datetime']
                if hasattr(price_time, 'tzinfo') and price_time.tzinfo:
                    price_time = price_time.astimezone(spain_tz)
                else:
                    price_time = spain_tz.localize(price_time)

                if price_time.hour == current_hour.hour and \
                        price_time.date() == current_hour.date():
                    return {
                        'price_eur_kwh': row['spot_price_eur_kwh'],
                        'price_eur_mwh': row['spot_price'],
                        'time': price_time,
                        'source': 'API' if row['spot_price'] != 0.15 else 'Fallback'
                    }

        return None
    except Exception as e:
        print(f"获取当前电价失败: {e}")
        return None

def display_price_trend():
    """
    显示每日逐小时电价趋势
    """
    try:
        st.markdown("### Daily Electricity Price Trend")

        # 获取今日电价数据
        today_prices = get_ree_price_with_fallback()

        if not today_prices.empty:
            # 创建图表
            fig = go.Figure()

            # 确保datetime列是datetime对象
            if not pd.api.types.is_datetime64_any_dtype(today_prices['datetime']):
                today_prices['datetime'] = pd.to_datetime(today_prices['datetime'])

            # 转换为西班牙时区
            spain_tz = pytz.timezone('Europe/Madrid')

            # 为所有时间添加时区信息
            today_prices['datetime_local'] = today_prices['datetime'].apply(
                lambda x: x.astimezone(spain_tz) if hasattr(x, 'tzinfo') and x.tzinfo else spain_tz.localize(x)
            )

            # 添加电价线
            fig.add_trace(go.Scatter(
                x=today_prices['datetime_local'],
                y=today_prices['spot_price_eur_kwh'] * 1000,  # 显示€/MWh
                mode='lines+markers',
                name='Electricity Price',
                line=dict(color='#FF6B6B', width=3),
                marker=dict(size=8, color='#FF6B6B'),
                hovertemplate='Time: %{x|%H:%M}<br>Price: %{y:.2f} €/MWh<extra></extra>'
            ))

            # 计算平均价格
            avg_price = today_prices['spot_price_eur_kwh'].mean() * 1000
            fig.add_hline(
                y=avg_price,
                line_dash="dash",
                line_color="green",
                opacity=0.7,
                annotation_text=f"Average: {avg_price:.2f} €/MWh",
                annotation_position="top right"
            )

            # 添加当前时间标记
            current_time = datetime.now(spain_tz)
            current_hour = current_time.replace(minute=0, second=0, microsecond=0)

            # 找到当前小时的价格
            current_price = None
            current_price_time = None

            for idx, row in today_prices.iterrows():
                price_time = row['datetime_local']
                if price_time.hour == current_hour.hour and price_time.date() == current_hour.date():
                    current_price = row['spot_price_eur_kwh'] * 1000
                    current_price_time = price_time
                    break

            if current_price is not None:
                # 添加垂直线
                fig.add_shape(
                    type="line",
                    x0=current_price_time,
                    y0=0,
                    x1=current_price_time,
                    y1=1,
                    yref="paper",
                    line=dict(color="red", width=2, dash="dot")
                )
                # 添加标注
                fig.add_annotation(
                    x=current_price_time,
                    y=1.02,  # 纸面坐标的1.02，即稍微高于图表顶部
                    yref="paper",
                    text=f"Current: {current_price:.2f} €/MWh",
                    showarrow=False,
                    font=dict(color="red", size=12),
                    bgcolor="white",
                    bordercolor="red",
                    borderwidth=1
                )

            fig.update_layout(
                template=chart_theme,
                height=400,
                xaxis_title="Time (24h)",
                yaxis_title="Price (€/MWh)",
                hovermode="x unified",
                showlegend=True,
                xaxis=dict(
                    tickformat="%H:%M",
                    tickmode="auto",
                    nticks=12  # 显示12个刻度（每2小时一个）
                ),
                title="24-Hour Electricity Price Trend",
                title_font_size=16
            )

            st.plotly_chart(fig, use_container_width=True)

            # 添加电价数据表格
            st.markdown("#### Price Table (Today)")

            # 准备表格数据
            table_data = []
            for idx, row in today_prices.iterrows():
                price_time = row['datetime_local']
                is_current = price_time.hour == current_hour.hour and price_time.date() == current_hour.date()

                table_data.append({
                    "Time": price_time.strftime("%H:%M"),
                    "Price (€/MWh)": f"{row['spot_price']:.2f}",
                    "Price (€/kWh)": f"{row['spot_price_eur_kwh']:.5f}",
                    "Current": "✓" if is_current else ""
                })

            price_df = pd.DataFrame(table_data)

            # 高亮当前小时
            def highlight_current(row):
                if row['Current'] == '✓':
                    return ['background-color: rgba(255, 107, 107, 0.2); font-weight: bold'] * 4
                return [''] * 4

            st.dataframe(
                price_df.style.apply(highlight_current, axis=1),
                use_container_width=True,
                hide_index=True,
                height=300
            )

            # 添加统计数据
            col1, col2, col3 = st.columns(3)
            with col1:
                min_price = today_prices['spot_price'].min()
                min_time_idx = today_prices['spot_price'].idxmin()
                min_time = today_prices.loc[min_time_idx, 'datetime_local']
                min_time_str = min_time.strftime("%H:%M")
                st.metric("Lowest Price", f"{min_price:.2f} €/MWh", f"at {min_time_str}")

            with col2:
                max_price = today_prices['spot_price'].max()
                max_time_idx = today_prices['spot_price'].idxmax()
                max_time = today_prices.loc[max_time_idx, 'datetime_local']
                max_time_str = max_time.strftime("%H:%M")
                st.metric("Highest Price", f"{max_price:.2f} €/MWh", f"at {max_time_str}")

            with col3:
                st.metric("Average Price", f"{avg_price:.2f} €/MWh")

            # 添加数据来源说明
            cost_data = update_electricity_cost()
            if cost_data and 'source' in cost_data:
                source = cost_data.get('source', 'Unknown')
                if source == 'Fallback':
                    st.warning("⚠️ Using fallback price data (0.15€/MWh)")
                else:
                    st.info("ℹ️ Data source: REE API (Spain)")

        else:
            st.warning("Unable to load electricity price data")

    except Exception as e:
        st.error(f"Error displaying price trend: {e}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")


def update_electricity_cost():
    """
    更新用电成本计算
    """
    try:
        # 获取当前电价
        current_price_data = get_current_hour_price()

        if current_price_data and st.session_state.current_data:
            # 计算总耗电量（千瓦时）
            voltage = 220.0  # 家用电压
            total_energy_kwh = 0.0

            # 电流数据是每5秒记录一次（与页面刷新频率一致）
            if len(st.session_state.current_data) >= 5:
                # 计算最近一次电流的平均值
                recent_currents = st.session_state.current_data[-10:]  # 最近10个数据点
                avg_current = np.mean(recent_currents) if recent_currents else 0.0

                # 实时功率 = 电压 × 电流
                power_watts = voltage * avg_current  # 瓦特
                power_kw = power_watts / 1000.0  # 千瓦

                # 假设页面每2秒刷新一次，计算这段时间的耗电量
                time_interval_hours = 2.0 / 3600.0  # 2秒转换为小时
                recent_energy_kwh = power_kw * time_interval_hours

                # 更新总耗电量
                if 'total_energy_kwh' not in st.session_state:
                    st.session_state.total_energy_kwh = 0.0

                st.session_state.total_energy_kwh += recent_energy_kwh

                # 计算成本
                cost_eur = st.session_state.total_energy_kwh * current_price_data['price_eur_kwh']

                return {
                    'current_price_eur_kwh': current_price_data['price_eur_kwh'],
                    'current_price_eur_mwh': current_price_data['price_eur_mwh'],
                    'current_power_kw': power_kw,
                    'total_energy_kwh': st.session_state.total_energy_kwh,
                    'total_cost_eur': cost_eur,
                    'time': current_price_data['time'],
                    'source': current_price_data.get('source', 'Unknown')
                }

        return None
    except Exception as e:
        print(f"计算用电成本失败: {e}")
        return None

# 主显示区域
col1, col2, col3 = st.columns([3, 1, 2])

with col1:
    st.markdown("### Temperature Monitoring")

    # 显示模式状态
    if st.session_state.current_mode == "AUTO":
        st.info(f"System Mode: AUTOMATIC (Controlled by Temp)")
    elif st.session_state.current_mode == "MANUAL":
        st.warning(f"System Mode: MANUAL OVERRIDE (Controlled by Telegram)")
    elif st.session_state.current_mode == "UNKNOWN":
        st.info("System Mode: Unknown")
    else:
        st.info("Waiting for mode data...")

    if st.session_state.temperature_data:
        current_temp = st.session_state.temperature_data[-1]

        if current_temp >= temp_danger:
            card_style = "background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);"
            status_text = "Temperature Danger!"
        elif current_temp >= temp_warning:
            card_style = "background: linear-gradient(135deg, #f9d423 0%, #ff4e50 100%);"
            status_text = "Temperature High"
        else:
            card_style = "background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);"
            status_text = "Temperature Normal"

        st.markdown(f"""
        <div style="{card_style} border-radius: 15px; padding: 30px; color: white; text-align: center;">
            <div style="font-size: 1.2rem; margin-bottom: 10px;">Current Temperature</div>
            <div style="font-size: 4rem; font-weight: bold;">{current_temp:.2f}°C</div>
            <div style="font-size: 1rem; margin-top: 15px;">
                {status_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="temp-card" style="text-align: center;">
            <div style="font-size: 1.2rem;">Waiting for data...</div>
            <div style="font-size: 3rem; font-weight: bold;">-- °C</div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("### Current")

    if st.session_state.current_data:
        current_value = st.session_state.current_data[-1]

        st.markdown(f"""
        <div class="current-card" style="text-align: center;">
            <div style="font-size: 1rem; margin-bottom: 10px;">RMS Current</div>
            <div style="font-size: 2.5rem; font-weight: bold;">{current_value:.5f}</div>
            <div style="font-size: 1rem; margin-top: 10px;">A</div>
            <div style="font-size: 0.8rem; margin-top: 15px; opacity: 0.8;">
                {current_value:.3f} A
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="current-card" style="text-align: center;">
            <div style="font-size: 1rem;">Waiting for data...</div>
            <div style="font-size: 2.5rem; font-weight: bold;">--</div>
            <div style="font-size: 1rem; margin-top: 10px;">A</div>
        </div>
        """, unsafe_allow_html=True)

with col3:
    st.markdown("### Electricity Cost")

    # 获取并显示电价和成本信息
    cost_data = update_electricity_cost()

    if cost_data:
        # 更新会话状态
        st.session_state.electricity_cost_data = {
            'current_price': cost_data['current_price_eur_kwh'],
            'total_energy': cost_data['total_energy_kwh'],
            'total_cost': cost_data['total_cost_eur'],
            'last_update': datetime.now()
        }

        # 显示电价卡片
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    border-radius: 15px; padding: 25px; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <div style="font-size: 1rem; margin-bottom: 10px;">Current Electricity Price</div>
            <div style="font-size: 2.5rem; font-weight: bold;">{cost_data['current_price_eur_kwh']:.4f}</div>
            <div style="font-size: 1rem; margin-top: 5px;">€/kWh</div>
            <div style="font-size: 0.8rem; margin-top: 10px; opacity: 0.8;">
                ({cost_data['current_price_eur_mwh']:.2f} €/MWh)
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 显示能耗和成本卡片
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                    border-radius: 15px; padding: 25px; color: white; margin-top: 20px; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <div style="font-size: 0.9rem;">Energy Consumed</div>
                    <div style="font-size: 1.8rem; font-weight: bold;">{cost_data['total_energy_kwh']:.3f}</div>
                    <div style="font-size: 0.8rem;">kWh</div>
                </div>
                <div>
                    <div style="font-size: 0.9rem;">Total Cost</div>
                    <div style="font-size: 1.8rem; font-weight: bold;">{cost_data['total_cost_eur']:.3f}</div>
                    <div style="font-size: 0.8rem;">€</div>
                </div>
            </div>
            <div style="font-size: 0.8rem; margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.2);">
                Current Power: {cost_data['current_power_kw']:.2f} kW<br>
                Updated: {cost_data['time'].strftime('%H:%M')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 添加重置按钮
        if st.button("Reset Energy Counter", use_container_width=True, type="secondary"):
            st.session_state.total_energy_kwh = 0.0
            st.session_state.electricity_cost_data['total_energy'] = 0.0
            st.session_state.electricity_cost_data['total_cost'] = 0.0
            st.rerun()
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    border-radius: 15px; padding: 25px; color: white; text-align: center;">
            <div style="font-size: 1rem;">Waiting for electricity price data...</div>
            <div style="font-size: 2.5rem; font-weight: bold;">--</div>
            <div style="font-size: 1rem; margin-top: 5px;">€/kWh</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                    border-radius: 15px; padding: 25px; color: white; margin-top: 20px; 
                    text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <div style="font-size: 1rem;">Waiting for current measurement...</div>
            <div style="font-size: 1.8rem; font-weight: bold; margin-top: 10px;">-- kWh</div>
            <div style="font-size: 0.8rem; margin-top: 5px;">Energy Consumed</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# 温度图表
st.markdown("### Temperature Trend")

if st.session_state.temperature_data:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=st.session_state.timestamps[-data_points:],
        y=st.session_state.temperature_data[-data_points:],
        mode='lines+markers',
        name='Temperature',
        line=dict(color='#2196F3', width=3),
        marker=dict(size=6, color='#2196F3'),
        hovertemplate='Time: %{x|%H:%M:%S}<br>Temp: %{y}°C<extra></extra>'
    ))

    fig.add_hline(
        y=temp_warning,
        line_dash="dash",
        line_color="orange",
        opacity=0.7,
        annotation_text=f"Warning: {temp_warning}°C",
        annotation_position="top right"
    )

    fig.add_hline(
        y=temp_danger,
        line_dash="dash",
        line_color="red",
        opacity=0.7,
        annotation_text=f"Danger: {temp_danger}°C",
        annotation_position="top right"
    )

    if len(st.session_state.temperature_data) > 10:
        avg_temp = sum(st.session_state.temperature_data[-data_points:]) / len(
            st.session_state.temperature_data[-data_points:])
        fig.add_hline(
            y=avg_temp,
            line_dash="dot",
            line_color="green",
            opacity=0.5,
            annotation_text=f"Average: {avg_temp:.1f}°C",
            annotation_position="bottom right"
        )

    fig.update_layout(
        template=chart_theme,
        height=400,
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        showlegend=True,
        title="Real-Time Temperature Monitoring",
        title_font_size=20
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    fig_empty = go.Figure()
    fig_empty.update_layout(
        height=400,
        template=chart_theme,
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        title="Awaiting Sensor Data..."
    )
    st.plotly_chart(fig_empty, use_container_width=True)

st.markdown("---")

# 电价趋势表格
display_price_trend()

st.markdown("---")

# 数据表格
st.markdown("### Recent Data Records")

if st.session_state.timestamps:
    data = {
        "Time": [ts.strftime("%H:%M:%S") for ts in st.session_state.timestamps[-20:]],
        "Temperature (°C)": st.session_state.temperature_data[-20:],
        "Current (A)": [f"{c:.5f}" for c in st.session_state.current_data[-20:]]
    }

    df = pd.DataFrame(data)


    def highlight_temp(row):
        if row['Temperature (°C)'] >= temp_danger:
            return ['background-color: #ffebee; color: #c62828; font-weight: bold'] * 3
        elif row['Temperature (°C)'] >= temp_warning:
            return ['background-color: #fff3e0; color: #ef6c00'] * 3
        else:
            return [''] * 3


    st.dataframe(
        df.style.apply(highlight_temp, axis=1),
        use_container_width=True,
        hide_index=True,
        height=400
    )

    st.markdown("#### Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Data Points", len(st.session_state.timestamps))

    with col2:
        if st.session_state.temperature_data:
            avg_temp = sum(st.session_state.temperature_data[-data_points:]) / len(
                st.session_state.temperature_data[-data_points:])
            st.metric("Average Temp", f"{avg_temp:.1f}°C")

    with col3:
        if st.session_state.temperature_data:
            max_temp = max(st.session_state.temperature_data[-data_points:])
            st.metric("Max Temp", f"{max_temp:.1f}°C")

    with col4:
        if st.button("Clear Data", use_container_width=True):
            st.session_state.temperature_data.clear()
            st.session_state.current_data.clear()
            st.session_state.timestamps.clear()
            st.session_state.current_mode = "WAITING"
            st.rerun()
else:
    st.info("Waiting for ESP32 sensor data...")


# 数据更新逻辑 - 每次页面加载都会执行
def update_data():
    if st.session_state.serial_connected:
        new_data = read_from_esp32_serial()
    else:
        new_data = read_from_esp32_simulation()

    if new_data:
        st.session_state.temperature_data.append(new_data['temperature'])
        st.session_state.current_data.append(new_data['current'])
        st.session_state.timestamps.append(new_data['timestamp'])
        st.session_state.current_mode = new_data.get('mode', st.session_state.current_mode)

        if len(st.session_state.temperature_data) > data_points:
            st.session_state.temperature_data.pop(0)
            st.session_state.current_data.pop(0)
            st.session_state.timestamps.pop(0)

        st.session_state.last_update = datetime.now()


# 执行数据更新
update_data()

# 底部状态栏
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.session_state.serial_connected:
        if st.session_state.serial_conn and st.session_state.serial_conn.is_open:
            st.success(f"ESP32 Connected to {com_port}")
        else:
            st.error("Serial connection lost")
            st.session_state.serial_connected = False
    else:
        st.warning("ESP32 Not Connected (Simulation Mode)")

with col2:
    st.markdown(f"**Update Time:** {st.session_state.last_update.strftime('%H:%M:%S')}")

with col3:
    # 添加自动刷新开关
    auto_refresh = st.toggle("Auto Refresh (5s)", value=True, key="auto_refresh")

    if st.button("Manual Refresh", use_container_width=True):
        update_data()
        st.rerun()

    # 显示自动刷新状态
    if auto_refresh:
        st.caption("Auto refresh enabled")
        # 使用Streamlit的自动刷新机制
        time.sleep(2)
        st.rerun()

# 数据导出
st.markdown("---")
st.markdown("#### Data Export")

if st.session_state.timestamps:
    export_df = pd.DataFrame({
        "Timestamp": st.session_state.timestamps,
        "Temperature (°C)": st.session_state.temperature_data,
        "Current (A)": st.session_state.current_data
    })

    col1, col2 = st.columns(2)

    with col1:
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"esp32_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        if st.button("Preview Data", use_container_width=True):
            st.dataframe(export_df.tail(10), use_container_width=True)
else:
    st.info("No data available for export.")

# 最后的状态信息
st.markdown(f"""
<div style="text-align: center; margin-top: 20px; padding: 10px; background-color: #396453; border-radius: 5px;">
    <small>ESP32 Temperature Monitoring System | Sensor Update: every 5s | UI Refresh: every 2s</small><br>
    <small>Data Format: Temp: XX.XX °C | Irms: X.XXXXX</small><br>
    <small>Current Mode: {st.session_state.current_mode} | Connection: {'Serial' if st.session_state.serial_connected else 'Simulation'}</small>
</div>
""", unsafe_allow_html=True)

# 页面自动刷新控制（2秒一次）
st.markdown(f"""
<script>
    setTimeout(function() {{
        window.location.reload();
    }}, 2000);
</script>
""", unsafe_allow_html=True)
