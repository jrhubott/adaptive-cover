"""Plotly chart generation for simulation results."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def generate_position_chart(results: list[dict]) -> str:
    """
    Generate interactive position over time chart.

    Args:
        results: List of simulation data points

    Returns:
        Plotly HTML div string
    """
    timestamps = [r["timestamp"] for r in results]
    positions = [r["position"] for r in results]
    sun_in_window = [r["sun_in_window"] for r in results]

    # Create colors based on sun_in_window
    colors = ["rgba(255, 165, 0, 0.7)" if siw else "rgba(128, 128, 128, 0.3)" for siw in sun_in_window]

    fig = go.Figure()

    # Add position trace
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=positions,
        mode="lines+markers",
        name="Position",
        line={"color": "blue", "width": 2},
        marker={"size": 4, "color": colors},
        hovertemplate="<b>%{x}</b><br>Position: %{y}%<extra></extra>",
    ))

    fig.update_layout(
        title="Cover Position Over Time",
        xaxis_title="Time",
        yaxis_title="Position (%)",
        hovermode="x unified",
        height=400,
        template="plotly_white",
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def generate_solar_chart(results: list[dict]) -> str:
    """
    Generate solar position chart (azimuth and elevation).

    Args:
        results: List of simulation data points

    Returns:
        Plotly HTML div string
    """
    timestamps = [r["timestamp"] for r in results]
    azimuths = [r["solar_azimuth"] for r in results]
    elevations = [r["solar_elevation"] for r in results]

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Solar Azimuth", "Solar Elevation"),
        vertical_spacing=0.12,
    )

    # Azimuth trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=azimuths,
            mode="lines",
            name="Azimuth",
            line={"color": "orange", "width": 2},
            hovertemplate="<b>%{x}</b><br>Azimuth: %{y}°<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Elevation trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=elevations,
            mode="lines",
            name="Elevation",
            line={"color": "red", "width": 2},
            hovertemplate="<b>%{x}</b><br>Elevation: %{y}°<extra></extra>",
        ),
        row=2,
        col=1,
    )

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Degrees", row=1, col=1)
    fig.update_yaxes(title_text="Degrees", row=2, col=1)

    fig.update_layout(
        height=600,
        showlegend=False,
        hovermode="x unified",
        template="plotly_white",
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def generate_sun_path_chart(results: list[dict], profile: dict) -> str:
    """
    Generate sun path diagram (polar chart).

    Args:
        results: List of simulation data points
        profile: Cover profile with window configuration

    Returns:
        Plotly HTML div string
    """
    azimuths = [r["solar_azimuth"] for r in results]
    elevations = [r["solar_elevation"] for r in results]
    sun_in_window = [r["sun_in_window"] for r in results]

    # Separate points inside and outside window
    azi_in = [a for a, siw in zip(azimuths, sun_in_window) if siw]
    elev_in = [90 - e for e, siw in zip(elevations, sun_in_window) if siw]  # Convert to polar radius

    azi_out = [a for a, siw in zip(azimuths, sun_in_window) if not siw]
    elev_out = [90 - e for e, siw in zip(elevations, sun_in_window) if not siw]

    fig = go.Figure()

    # Sun path outside window
    if azi_out:
        fig.add_trace(go.Scatterpolar(
            r=elev_out,
            theta=azi_out,
            mode="lines+markers",
            name="Outside Window",
            line={"color": "gray", "width": 1},
            marker={"size": 3, "color": "gray"},
        ))

    # Sun path inside window
    if azi_in:
        fig.add_trace(go.Scatterpolar(
            r=elev_in,
            theta=azi_in,
            mode="lines+markers",
            name="Inside Window FOV",
            line={"color": "orange", "width": 2},
            marker={"size": 4, "color": "orange"},
        ))

    # Add window field of view
    window_azi = profile.get("window_azimuth", 180)
    fov_left = profile.get("fov_left", 90)
    fov_right = profile.get("fov_right", 90)

    # Draw FOV boundaries
    left_azi = (window_azi - fov_left) % 360
    right_azi = (window_azi + fov_right) % 360

    fig.add_trace(go.Scatterpolar(
        r=[0, 90],
        theta=[left_azi, left_azi],
        mode="lines",
        name="FOV Left",
        line={"color": "blue", "width": 1, "dash": "dash"},
    ))

    fig.add_trace(go.Scatterpolar(
        r=[0, 90],
        theta=[right_azi, right_azi],
        mode="lines",
        name="FOV Right",
        line={"color": "blue", "width": 1, "dash": "dash"},
    ))

    # Add window center direction
    fig.add_trace(go.Scatterpolar(
        r=[0, 90],
        theta=[window_azi, window_azi],
        mode="lines",
        name="Window Center",
        line={"color": "green", "width": 2},
    ))

    fig.update_layout(
        title="Sun Path Diagram",
        polar={
            "radialaxis": {
                "title": "Zenith Angle (°)",
                "range": [0, 90],
                "tickvals": [0, 30, 60, 90],
            },
            "angularaxis": {
                "title": "Azimuth",
                "direction": "clockwise",
                "rotation": 90,
            },
        },
        height=500,
        showlegend=True,
        template="plotly_white",
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def generate_combined_chart(results: list[dict]) -> str:
    """
    Generate combined chart with position and solar data.

    Args:
        results: List of simulation data points

    Returns:
        Plotly HTML div string
    """
    timestamps = [r["timestamp"] for r in results]
    positions = [r["position"] for r in results]
    azimuths = [r["solar_azimuth"] for r in results]
    elevations = [r["solar_elevation"] for r in results]

    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=("Cover Position", "Solar Azimuth", "Solar Elevation"),
        vertical_spacing=0.08,
        row_heights=[0.4, 0.3, 0.3],
    )

    # Position trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=positions,
            mode="lines",
            name="Position",
            line={"color": "blue", "width": 2},
            hovertemplate="<b>%{x}</b><br>Position: %{y}%<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Azimuth trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=azimuths,
            mode="lines",
            name="Azimuth",
            line={"color": "orange", "width": 1.5},
            hovertemplate="<b>%{x}</b><br>Azimuth: %{y}°<extra></extra>",
        ),
        row=2,
        col=1,
    )

    # Elevation trace
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=elevations,
            mode="lines",
            name="Elevation",
            line={"color": "red", "width": 1.5},
            hovertemplate="<b>%{x}</b><br>Elevation: %{y}°<extra></extra>",
        ),
        row=3,
        col=1,
    )

    fig.update_xaxes(title_text="Time", row=3, col=1)
    fig.update_yaxes(title_text="Position (%)", row=1, col=1)
    fig.update_yaxes(title_text="Degrees", row=2, col=1)
    fig.update_yaxes(title_text="Degrees", row=3, col=1)

    fig.update_layout(
        height=800,
        showlegend=False,
        hovermode="x unified",
        template="plotly_white",
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")
