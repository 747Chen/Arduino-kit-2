import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta


@st.cache_data #this will cache the data generation for performance
def create_sample_data():
    """
    Generate realistic synthetic market data for visualization examples

    Returns:
        pd.DataFrame: Sample data with multiple features
    """
    # Generate date range
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='H')
    n_points = len(dates)
    # Set random seed for reproducibility
    np.random.seed(42)
    # Generate realistic patterns
    hours = np.arange(n_points)
    # Daily pattern (24-hour cycle)
    daily_pattern = 30 * np.sin(2 * np.pi * hours / 24)
    # Weekly pattern
    weekly_pattern = 10 * np.sin(2 * np.pi * hours / (24 * 7))
    # Random noise
    noise = np.random.normal(0, 5, n_points)
    # Create price with patterns
    base_price = 50
    price = base_price + daily_pattern + weekly_pattern + noise
    price = np.clip(price, 10, 100)  # Keep realistic bounds
    # Create demand (inverse relationship with price for realism)
    base_demand = 1000
    demand_pattern = 200 * np.sin(2 * np.pi * hours / 24 + np.pi)  # Peak opposite to price
    demand = base_demand + demand_pattern + np.random.normal(0, 30, n_points)
    demand = np.clip(demand, 700, 1400)
    # Create renewable percentage
    renewable = np.random.uniform(15, 85, n_points)
    # Create regions
    regions = np.random.choice(['North', 'South', 'East', 'West'], n_points)
    # Create temperature (affects demand)
    temp_base = 20
    temp_seasonal = 10 * np.sin(2 * np.pi * hours / (24 * 365))
    temperature = temp_base + temp_seasonal + np.random.normal(0, 3, n_points)

    # Assemble DataFrame
    df = pd.DataFrame({
        'datetime': dates,
        'date': dates.date,
        'hour': dates.hour,
        'day_of_week': dates.dayofweek,
        'month': dates.month,
        'price': price,
        'demand': demand,
        'renewable_pct': renewable,
        'region': regions,
        'temperature': temperature
    })

    return df


# Load data
df = create_sample_data()

st.title("📊 Streamlit Visualization Tutorial")
st.markdown("---")

st.header("Slide 16: Simple Native Charts")

st.write("""
Streamlit's native charts are the fastest way to visualize data. 
They require minimal code and work great for exploration!
""")

# Prepare data for native charts (needs datetime index)
daily_avg = df.groupby('date').agg({
    'price': 'mean',
    'demand': 'mean',
    'renewable_pct': 'mean'
}).reset_index()

# Example 1: Line Chart
st.subheader("1️⃣ Line Chart - Perfect for Time Series")
st.write("Best for showing trends over time")

col1, col2 = st.columns([2, 1])

with col1:
    st.line_chart(daily_avg.set_index('date')['price'])

with col2:
    st.code("""
st.line_chart(
    df.set_index('date')['price']
)
""", language="python")

# Example 2: Bar Chart
st.subheader("2️⃣ Bar Chart - Perfect for Comparisons")
st.write("Best for comparing values across categories")

# Monthly average prices
monthly_avg = df.groupby('month')['price'].mean()

col1, col2 = st.columns([2, 1])

with col1:
    st.bar_chart(monthly_avg)

with col2:
    st.code("""
st.bar_chart(
    monthly_data
)
""", language="python")

# Example 3: Area Chart
st.subheader("3️⃣ Area Chart - Perfect for Multiple Series")
st.write("Best for showing magnitude and composition")

col1, col2 = st.columns([2, 1])

with col1:
    # Show first 30 days
    display_data = daily_avg.head(30).set_index('date')[['price', 'demand']]
    # Normalize to same scale for better visualization
    display_data['price_scaled'] = display_data['price'] * 10
    st.area_chart(display_data[['price_scaled', 'demand']])

with col2:
    st.code("""
st.area_chart(
    df[['series1', 'series2']]
)
""", language="python")

st.info("💡 **Pro Tip:** Native charts automatically handle DataFrame columns and create legends!")

# ============================================================================
# PLOTLY INTEGRATION
# ============================================================================

st.markdown("---")
st.header("Slide 17: Plotly Integration")

st.write("""
Plotly creates **interactive, professional visualizations** with hover tooltips, 
zooming, panning, and beautiful styling. Perfect for production dashboards!
""")

# Example 1: Basic Plotly Line Chart
st.subheader("1️⃣ Basic Interactive Line Chart")

col1, col2 = st.columns([2, 1])

with col1:
    # Create figure
    fig_basic = px.line(
        daily_avg.head(90),  # First 3 months
        x='date',
        y='price',
        title='Electricity Price - First Quarter 2024',
        labels={'price': 'Price (€/MWh)', 'date': 'Date'}
    )

    # Customize layout
    fig_basic.update_layout(
        hovermode='x unified',
        plot_bgcolor='white'
    )

    st.plotly_chart(fig_basic, use_container_width=True)

    st.write("👆 **Try it!** Hover, zoom, pan, double-click to reset")

with col2:
    st.code("""
import plotly.express as px

fig = px.line(
    df,
    x='date',
    y='price',
    title='My Chart',
    labels={
        'price': 'Price (€/MWh)'
    }
)

st.plotly_chart(fig)
""", language="python")

# Example 2: Multiple Traces
st.subheader("2️⃣ Multiple Series with Dual Axes")

col1, col2 = st.columns([2, 1])

with col1:
    # Create figure with secondary y-axis
    fig_dual = go.Figure()

    # Add price trace
    fig_dual.add_trace(
        go.Scatter(
            x=daily_avg.head(60)['date'],
            y=daily_avg.head(60)['price'],
            name='Price',
            line=dict(color='#FF6B6B', width=2)
        )
    )

    # Add demand trace with secondary y-axis
    fig_dual.add_trace(
        go.Scatter(
            x=daily_avg.head(60)['date'],
            y=daily_avg.head(60)['demand'],
            name='Demand',
            yaxis='y2',
            line=dict(color='#4ECDC4', width=2)
        )
    )

    # Update layout for dual axes
    fig_dual.update_layout(
        title='Price vs Demand - First 60 Days',
        xaxis=dict(title='Date'),
        yaxis=dict(title='Price (€/MWh)', side='left'),
        yaxis2=dict(title='Demand (MW)', side='right', overlaying='y'),
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig_dual, use_container_width=True)

with col2:
    st.code("""
import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df['date'],
        y=df['price'],
        name='Price'
    )
)

fig.add_trace(
    go.Scatter(
        x=df['date'],
        y=df['demand'],
        name='Demand',
        yaxis='y2'
    )
)

fig.update_layout(
    yaxis2=dict(
        overlaying='y',
        side='right'
    )
)

st.plotly_chart(fig)
""", language="python")

# Example 3: Scatter Plot with Trend
st.subheader("3️⃣ Scatter Plot with Trendline")

col1, col2 = st.columns([2, 1])

with col1:
    # Sample data for scatter
    scatter_data = df.groupby('temperature')['price'].mean().reset_index()

    fig_scatter = px.scatter(
        df.sample(500),  # Sample for performance
        x='temperature',
        y='price',
        color='region',
        title='Temperature vs Price by Region',
        labels={
            'temperature': 'Temperature (°C)',
            'price': 'Price (€/MWh)',
            'region': 'Region'
        },
        trendline='ols',  # Add trendline
        opacity=0.6
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:
    st.code("""
fig = px.scatter(
    df,
    x='temperature',
    y='price',
    color='region',
    trendline='ols',
    opacity=0.6
)

st.plotly_chart(fig)
""", language="python")

st.success("""
**Why Plotly?**
- 🖱️ Built-in interactivity (zoom, pan, hover)
- 🎨 Professional styling out of the box
- 📊 Supports complex visualizations
- 📱 Responsive and mobile-friendly
""")

# ============================================================================
# MATPLOTLIB/SEABORN
# ============================================================================

st.markdown("---")
st.header("Slide 19: Matplotlib & Seaborn")

st.write("""
Matplotlib and Seaborn are perfect for **statistical visualizations** and 
**publication-quality** static plots. Use when you need fine-grained control 
or specific statistical plots.
""")

# Example 1: Basic Matplotlib
st.subheader("1️⃣ Basic Matplotlib Plot")

col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(10, 4))

    # Plot data
    ax.plot(daily_avg.head(30)['date'],
            daily_avg.head(30)['price'],
            color='#FF6B6B',
            linewidth=2,
            marker='o',
            markersize=4)

    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price (€/MWh)', fontsize=12)
    ax.set_title('Electricity Price - January 2024', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)
    plt.close()

with col2:
    st.code("""
import matplotlib.pyplot as plt

fig, ax = plt.subplots()

ax.plot(
    df['date'], 
    df['price'],
    linewidth=2
)

ax.set_xlabel('Date')
ax.set_ylabel('Price')
ax.set_title('My Chart')
ax.grid(True)

st.pyplot(fig)
""", language="python")

# Example 2: Seaborn Statistical Plot
st.subheader("2️⃣ Seaborn - Distribution Plot")

col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(10, 4))

    # Create histogram with KDE
    sns.histplot(
        data=df,
        x='price',
        hue='region',
        kde=True,
        ax=ax,
        bins=30,
        alpha=0.6
    )

    ax.set_xlabel('Price (€/MWh)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Price Distribution by Region', fontsize=14, fontweight='bold')

    plt.tight_layout()

    st.pyplot(fig)
    plt.close()

with col2:
    st.code("""
import seaborn as sns

fig, ax = plt.subplots()

sns.histplot(
    data=df,
    x='price',
    hue='region',
    kde=True,
    bins=30,
    ax=ax
)

st.pyplot(fig)
""", language="python")

# Example 3: Seaborn Heatmap
st.subheader("3️⃣ Seaborn - Correlation Heatmap")

col1, col2 = st.columns([2, 1])

with col1:
    # Calculate correlation
    corr_data = df[['price', 'demand', 'renewable_pct', 'temperature']].corr()

    fig, ax = plt.subplots(figsize=(8, 6))

    sns.heatmap(
        corr_data,
        annot=True,
        fmt='.2f',
        cmap='coolwarm',
        center=0,
        square=True,
        linewidths=1,
        ax=ax,
        cbar_kws={'label': 'Correlation'}
    )

    ax.set_title('Feature Correlation Matrix', fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()

    st.pyplot(fig)
    plt.close()

with col2:
    st.code("""
import seaborn as sns

corr = df.corr()

fig, ax = plt.subplots()

sns.heatmap(
    corr,
    annot=True,
    fmt='.2f',
    cmap='coolwarm',
    ax=ax
)

st.pyplot(fig)
""", language="python")

# Example 4: Subplots
st.subheader("4️⃣ Multiple Subplots")

col1, col2 = st.columns([2, 1])

with col1:
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Plot 1: Price over time
    axes[0, 0].plot(daily_avg.head(30)['date'], daily_avg.head(30)['price'], 'r-')
    axes[0, 0].set_title('Price Trend')
    axes[0, 0].set_ylabel('Price (€/MWh)')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].tick_params(axis='x', rotation=45)

    # Plot 2: Demand over time
    axes[0, 1].plot(daily_avg.head(30)['date'], daily_avg.head(30)['demand'], 'b-')
    axes[0, 1].set_title('Demand Trend')
    axes[0, 1].set_ylabel('Demand (MW)')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].tick_params(axis='x', rotation=45)

    # Plot 3: Price distribution
    axes[1, 0].hist(df['price'], bins=50, color='red', alpha=0.7, edgecolor='black')
    axes[1, 0].set_title('Price Distribution')
    axes[1, 0].set_xlabel('Price (€/MWh)')
    axes[1, 0].set_ylabel('Frequency')

    # Plot 4: Scatter
    axes[1, 1].scatter(df.sample(500)['temperature'],
                       df.sample(500)['price'],
                       alpha=0.5,
                       color='purple')
    axes[1, 1].set_title('Temperature vs Price')
    axes[1, 1].set_xlabel('Temperature (°C)')
    axes[1, 1].set_ylabel('Price (€/MWh)')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()

    st.pyplot(fig)
    plt.close()

with col2:
    st.code("""
fig, axes = plt.subplots(
    2, 2, 
    figsize=(12, 8)
)

# Top left
axes[0, 0].plot(x1, y1)
axes[0, 0].set_title('Plot 1')

# Top right
axes[0, 1].plot(x2, y2)
axes[0, 1].set_title('Plot 2')

# Bottom left
axes[1, 0].hist(data)
axes[1, 0].set_title('Plot 3')

# Bottom right
axes[1, 1].scatter(x, y)
axes[1, 1].set_title('Plot 4')

plt.tight_layout()
st.pyplot(fig)
""", language="python")

st.warning("""
**⚠️ Important:** Always call `plt.close()` after `st.pyplot(fig)` to free memory!
""")

st.info("""
**When to use Matplotlib/Seaborn:**
- 📄 Academic papers and reports
- 📊 Complex statistical visualizations
- 🎨 Need pixel-perfect control
- 📈 Specific plot types (violin, box, pair plots)
""")

# ============================================================================
# COMPARISON SUMMARY
# ============================================================================

st.markdown("---")
st.header("📋 Visualization Comparison Summary")

comparison_df = pd.DataFrame({
    'Feature': ['Setup Time', 'Interactivity', 'Customization', 'Best For', 'Learning Curve'],
    'Native Charts': ['⚡ Instant', '⭐ Basic', '⭐ Limited', 'Quick exploration', '⭐ Easy'],
    'Plotly': ['⚡ Fast', '⭐⭐⭐ Excellent', '⭐⭐⭐ High', 'Production dashboards', '⭐⭐ Medium'],
    'Matplotlib': ['⏱️ Slower', '❌ None', '⭐⭐⭐ Complete', 'Publications', '⭐⭐⭐ Advanced']
})

st.dataframe(comparison_df, use_container_width=True, hide_index=True)

st.success("""
**🎯 Recommendation:** 
1. Start with **Native charts** for exploration
2. Use **Plotly** for production dashboards (90% of use cases)
3. Use **Matplotlib** for statistical analysis and publications
""")
