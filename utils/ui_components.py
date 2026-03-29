import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

def metric_card(title: str, value: str, dark_mode: bool = False):
    """
    Renders a custom CSS metric card.
    Note: Requires the CSS from assets/style.css to be loaded in the app.
    """
    dark_class = "dark" if dark_mode else ""
    # Injecting HTML for the card
    html = f"""
    <div class="metric-card {dark_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def create_pie_chart(labels, values, title):
    """Creates a stylized Plotly pie chart"""
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4)])
    fig.update_layout(
        title=title,
        margin=dict(t=40, b=0, l=0, r=0),
        font=dict(family="Inter, sans-serif")
    )
    return fig

def create_bar_chart(df, x_col, y_col, title, labels=None):
    """Creates a stylized Plotly bar chart"""
    fig = px.bar(df, x=x_col, y=y_col, title=title, labels=labels)
    fig.update_layout(
        margin=dict(t=40, b=0, l=0, r=0),
        font=dict(family="Inter, sans-serif"),
        xaxis_title="",
        yaxis_title=""
    )
    fig.update_traces(marker_color='#3b82f6', marker_line_color='#2563eb', marker_line_width=1.5, opacity=0.8)
    return fig

def create_line_chart(df, x_col, y_col, title):
    """Creates a stylized Plotly line chart"""
    fig = px.line(df, x=x_col, y=y_col, title=title)
    fig.update_layout(
        margin=dict(t=40, b=0, l=0, r=0),
        font=dict(family="Inter, sans-serif")
    )
    fig.update_traces(line_color='#10b981', line_width=3)
    return fig
