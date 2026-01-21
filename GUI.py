# 口令：streamlit run GUI.py
# TODO: ++data auto storage
# TODO: ++electricity price calculation, ++API get electricity price
# 接线指南：
# 16bit接IIC， 电流传感器接16bit的A1蓝色接口
# LED指示灯接D5绿色和黑色口， relay接D7
# 温度传感器接A3口
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import random
from datetime import datetime
import time
import serial
import queue
import regex as re

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
        temp = 0
        current = 0

        # 模拟模式切换
        current_time = time.time()
        mode = "AUTO" if int(current_time) % 10 < 5 else "MANUAL"

        return {
            "temperature": round(temp, 2),
            "current": round(current, 5),
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

# 主显示区域
col1, col2 = st.columns([3, 1])

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
