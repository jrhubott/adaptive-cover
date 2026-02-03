"""Flask web application for Adaptive Cover Pro simulation."""

import json
from datetime import date
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, Response, url_for

from lib.charts import (
    generate_combined_chart,
    generate_position_chart,
    generate_solar_chart,
    generate_sun_path_chart,
)
from lib.simulator import Simulator

app = Flask(__name__)
app.secret_key = "dev-key-change-in-production"

# Configuration
CONFIG_DIR = Path(__file__).parent / "config"
PROFILES_FILE = CONFIG_DIR / "profiles.json"

# In-memory cache for simulations
simulation_cache = {}
next_sim_id = 1


def load_profiles() -> dict:
    """Load profiles from JSON file."""
    if PROFILES_FILE.exists():
        with open(PROFILES_FILE) as f:
            return json.load(f)
    return {}


def save_profiles(profiles: dict) -> None:
    """Save profiles to JSON file."""
    CONFIG_DIR.mkdir(exist_ok=True)
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


@app.route("/")
def index():
    """Home page with profile list."""
    profiles = load_profiles()
    return render_template("index.html", profiles=profiles)


@app.route("/configure", methods=["GET", "POST"])
def configure():
    """Configuration form."""
    if request.method == "POST":
        # Save profile
        profiles = load_profiles()
        profile_id = request.form["profile_id"]

        # Build profile dictionary
        profile = {
            "name": request.form["name"],
            "cover_type": request.form["cover_type"],
            "latitude": float(request.form["latitude"]),
            "longitude": float(request.form["longitude"]),
            "timezone": request.form["timezone"],
            "window_azimuth": float(request.form["window_azimuth"]),
            "fov_left": float(request.form.get("fov_left", 90)),
            "fov_right": float(request.form.get("fov_right", 90)),
            "default_position": int(request.form.get("default_position", 60)),
            "min_position": int(request.form.get("min_position", 0)),
            "max_position": int(request.form.get("max_position", 100)),
            "enable_min_position": request.form.get("enable_min_position") == "on",
            "enable_max_position": request.form.get("enable_max_position") == "on",
            "sunset_position": int(request.form.get("sunset_position", 0)),
            "sunset_offset": int(request.form.get("sunset_offset", 0)),
            "sunrise_offset": int(request.form.get("sunrise_offset", 0)),
            "climate_mode": request.form.get("climate_mode") == "on",
            "min_elevation": float(request.form.get("min_elevation", 0)),
            "max_elevation": float(request.form.get("max_elevation", 90)),
        }

        # Add cover-specific parameters
        cover_type = request.form["cover_type"]
        if cover_type == "cover_blind":
            profile.update({
                "window_height": float(request.form.get("window_height", 2.1)),
                "distance": float(request.form.get("distance", 0.5)),
            })
        elif cover_type == "cover_awning":
            profile.update({
                "length": float(request.form.get("length", 2.1)),
                "angle": float(request.form.get("angle", 0)),
                "window_height": float(request.form.get("window_height", 2.1)),
                "distance": float(request.form.get("distance", 0.5)),
            })
        elif cover_type == "cover_tilt":
            profile.update({
                "slat_depth": float(request.form.get("slat_depth", 3)),
                "slat_distance": float(request.form.get("slat_distance", 2)),
                "inverse_state": request.form.get("inverse_state") == "on",
                "tilt_mode": request.form.get("tilt_mode", "mode2"),
            })

        profiles[profile_id] = profile
        save_profiles(profiles)

        flash(f"Profile '{profile['name']}' saved successfully!", "success")
        return redirect(url_for("index"))

    # GET request - show form
    profile_id = request.args.get("profile_id")
    profile = None
    if profile_id:
        profiles = load_profiles()
        profile = profiles.get(profile_id)

    return render_template("configure.html", profile=profile, profile_id=profile_id)


@app.route("/delete/<profile_id>", methods=["POST"])
def delete_profile(profile_id):
    """Delete a profile."""
    profiles = load_profiles()
    if profile_id in profiles:
        profile_name = profiles[profile_id]["name"]
        del profiles[profile_id]
        save_profiles(profiles)
        flash(f"Profile '{profile_name}' deleted.", "success")
    return redirect(url_for("index"))


@app.route("/simulate", methods=["POST"])
def simulate():
    """Run simulation."""
    global next_sim_id

    profile_id = request.form["profile_id"]
    sim_date = request.form.get("date", str(date.today()))
    interval = int(request.form.get("interval", 5))

    profiles = load_profiles()
    if profile_id not in profiles:
        flash("Profile not found!", "danger")
        return redirect(url_for("index"))

    profile = profiles[profile_id]

    try:
        # Run simulation
        simulator = Simulator()
        results = simulator.run(profile, sim_date, interval)

        # Cache results
        sim_id = next_sim_id
        next_sim_id += 1
        simulation_cache[sim_id] = {
            "profile": profile,
            "profile_id": profile_id,
            "date": sim_date,
            "interval": interval,
            "results": results,
            "simulator": simulator,
        }

        return redirect(url_for("results", sim_id=sim_id))

    except Exception as e:
        flash(f"Simulation error: {e!s}", "danger")
        return redirect(url_for("index"))


@app.route("/results/<int:sim_id>")
def results(sim_id):
    """Display simulation results."""
    if sim_id not in simulation_cache:
        flash("Simulation not found!", "danger")
        return redirect(url_for("index"))

    sim_data = simulation_cache[sim_id]

    # Generate charts
    position_chart = generate_position_chart(sim_data["results"])
    solar_chart = generate_solar_chart(sim_data["results"])
    sun_path_chart = generate_sun_path_chart(sim_data["results"], sim_data["profile"])
    combined_chart = generate_combined_chart(sim_data["results"])

    return render_template(
        "results.html",
        sim_id=sim_id,
        profile=sim_data["profile"],
        profile_id=sim_data["profile_id"],
        date=sim_data["date"],
        interval=sim_data["interval"],
        num_points=len(sim_data["results"]),
        position_chart=position_chart,
        solar_chart=solar_chart,
        sun_path_chart=sun_path_chart,
        combined_chart=combined_chart,
    )


@app.route("/export/<int:sim_id>/<format>")
def export(sim_id, format):
    """Export simulation results."""
    if sim_id not in simulation_cache:
        return "Simulation not found", 404

    sim_data = simulation_cache[sim_id]
    simulator = sim_data["simulator"]

    if format == "json":
        return Response(
            simulator.export_json(),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename=simulation_{sim_id}.json"},
        )
    elif format == "csv":
        return Response(
            simulator.export_csv(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=simulation_{sim_id}.csv"},
        )
    else:
        return "Unknown format", 400


if __name__ == "__main__":
    import os

    # Create config directory if it doesn't exist
    CONFIG_DIR.mkdir(exist_ok=True)

    # Allow port to be set via environment variable or default to 5000
    port = int(os.environ.get("FLASK_PORT", 5000))

    print("=" * 60)
    print("Adaptive Cover Pro - Simulation Web Application")
    print("=" * 60)
    print()
    print("Starting Flask development server...")
    print(f"Access the application at: http://localhost:{port}")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)

    app.run(debug=True, port=port)
