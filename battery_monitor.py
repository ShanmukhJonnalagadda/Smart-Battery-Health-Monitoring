

"""Beginner-friendly simulated Battery Health Monitoring System.

Readings are entered manually. This is an educational tool, not a certified BMS.
"""

import csv
import math
from datetime import datetime
from pathlib import Path

# Example thresholds for learning; these are not universal safety limits.
MIN_VOLTAGE = 3.2
MAX_VOLTAGE = 4.2
MIN_TEMPERATURE = 15.0
MAX_TEMPERATURE = 40.0
CRITICAL_BELOW_VOLTAGE = 3.0
CRITICAL_ABOVE_TEMPERATURE = 50.0

DATA_FILE = Path(__file__).with_name("battery_readings.csv")
CHART_FILE = Path(__file__).with_name("battery_chart.png")
COLUMNS = [
    "timestamp", "battery_id", "voltage_v", "current_a",
    "temperature_c", "power_w", "voltage_status",
    "temperature_status", "battery_status",
]


def get_number(prompt, allow_negative=False):
    """Ask until the user enters a valid, finite number."""
    while True:
        try:
            value = float(input(prompt))
        except ValueError:
            print("Please enter a number, such as 3.8 or 25.")
            continue

        if not math.isfinite(value):
            print("Please enter a finite number.")
        elif value < 0 and not allow_negative:
            print("This value cannot be negative in our simulation.")
        else:
            return value


def voltage_status(voltage):
    if voltage < MIN_VOLTAGE:
        return "Low"
    elif voltage <= MAX_VOLTAGE:
        return "Normal"
    else:
        return "High"


def temperature_status(temperature):
    if temperature < MIN_TEMPERATURE:
        return "Too Cold"
    elif temperature <= MAX_TEMPERATURE:
        return "Normal"
    else:
        return "High"


def battery_status(voltage, temperature):
    """Critical takes priority over Warning, which takes priority over Healthy."""
    if voltage < CRITICAL_BELOW_VOLTAGE or temperature > CRITICAL_ABOVE_TEMPERATURE:
        return "CRITICAL"
    elif MIN_VOLTAGE <= voltage <= MAX_VOLTAGE and MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE:
        return "HEALTHY"
    else:
        return "WARNING"


def save_reading(reading):
    """Append one reading to CSV, writing column names on the first save."""
    is_new_file = not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0
    with DATA_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        if is_new_file:
            writer.writeheader()
        writer.writerow(reading)


def load_readings():
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def take_reading():
    print("\n--- New battery reading ---")
    battery_id = input("Enter battery ID (e.g., 101): ").strip() or "101"
    voltage = get_number("Enter battery voltage (V): ")
    current = get_number("Enter battery current (A): ")
    temperature = get_number("Enter battery temperature (C): ", allow_negative=True)

    # Power is calculated rather than typed in by the user.
    power = voltage * current
    v_status = voltage_status(voltage)
    t_status = temperature_status(temperature)
    health = battery_status(voltage, temperature)

    print("\n--- Results ---")
    print("Battery ID:", battery_id)
    print(f"Voltage: {voltage:.2f} V  ({v_status})")
    print(f"Current: {current:.2f} A")
    print(f"Temperature: {temperature:.2f} C  ({t_status})")
    print(f"Power: {power:.2f} W")
    print("Battery Status:", health)

    reading = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "battery_id": battery_id,
        "voltage_v": f"{voltage:.2f}",
        "current_a": f"{current:.2f}",
        "temperature_c": f"{temperature:.2f}",
        "power_w": f"{power:.2f}",
        "voltage_status": v_status,
        "temperature_status": t_status,
        "battery_status": health,
    }
    save_reading(reading)
    print("Reading saved to", DATA_FILE.name)


def show_history():
    readings = load_readings()
    if not readings:
        print("\nNo readings saved yet. Choose option 1 first.")
        return

    print("\n--- Last five saved readings ---")
    for row in readings[-5:]:
        print(
            f"{row['timestamp']} | Battery {row['battery_id']} | "
            f"{row['voltage_v']} V | {row['temperature_c']} C | "
            f"{row['battery_status']}"
        )


def show_summary():
    readings = load_readings()
    if not readings:
        print("\nNo readings saved yet. Choose option 1 first.")
        return

    healthy = sum(row["battery_status"] == "HEALTHY" for row in readings)
    warning = sum(row["battery_status"] == "WARNING" for row in readings)
    critical = sum(row["battery_status"] == "CRITICAL" for row in readings)
    average_voltage = sum(float(row["voltage_v"]) for row in readings) / len(readings)
    average_temperature = sum(float(row["temperature_c"]) for row in readings) / len(readings)

    print("\n--- Monitoring summary (all saved batteries/readings) ---")
    print("Total readings:", len(readings))
    print("HEALTHY:", healthy)
    print("WARNING:", warning)
    print("CRITICAL:", critical)
    print(f"Average voltage: {average_voltage:.2f} V")
    print(f"Average temperature: {average_temperature:.2f} C")


def analyze_readings():
    readings = load_readings()

    if not readings:
        print("No battery readings available.")
        return

    # Collect voltage and temperature values
    voltages = [float(row["voltage_v"]) for row in readings]
    temperatures = [float(row["temperature_c"]) for row in readings]

    # Count healthy readings
    healthy_count = sum(
        row["battery_status"] == "HEALTHY"
        for row in readings
    )

    # Calculate percentage of healthy readings
    healthy_percentage = (healthy_count / len(readings)) * 100

    # Display analysis results
    print("\n--- Battery Data Analysis ---")
    print("Total readings:", len(readings))
    print(f"Lowest voltage: {min(voltages):.2f} V")
    print(f"Highest voltage: {max(voltages):.2f} V")
    print(f"Highest temperature: {max(temperatures):.2f} C")
    print(f"Healthy readings: {healthy_percentage:.1f}%")


    while True:
        print("\n1. Take a battery reading")
        print("2. View the last five readings")
        print("3. View monitoring summary")
        print("4. Make a graph")
        print("5. Analyze battery data")
        print("6. Exit")

        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            take_reading()
        elif choice == "2":
            show_history()
        elif choice == "3":
            show_summary()
        elif choice == "4":
            make_chart()
        elif choice == "5":
            analyze_readings()
        elif choice == "6":
            print("Battery Monitoring Stopped")
            break
        else:
            print("Please enter a number from 1 to 6.")


def make_chart():
    readings = load_readings()
    if not readings:
        print("\nNo readings saved yet. Choose option 1 first.")
        return

    # Matplotlib is only needed for charts. The rest runs without it.
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Install chart support first: python -m pip install matplotlib")
        return

    numbers = list(range(1, len(readings) + 1))
    voltage = [float(row["voltage_v"]) for row in readings]
    current = [float(row["current_a"]) for row in readings]
    temperature = [float(row["temperature_c"]) for row in readings]

    figure, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    for axis, values, title, unit in zip(
        axes,
        (voltage, current, temperature),
        ("Voltage", "Current", "Temperature"),
        ("V", "A", "C"),
    ):
        axis.plot(numbers, values, marker="o")
        axis.set_ylabel(unit)
        axis.set_title(title)
        axis.grid(True)
    axes[-1].set_xlabel("Saved reading number")
    figure.suptitle("Battery Monitoring History")
    figure.tight_layout()
    figure.savefig(CHART_FILE, dpi=150)
    print("Chart saved to", CHART_FILE.name)
    plt.show()
    plt.close(figure)



def main():
    print("Smart Battery Health Monitoring System")
    print("Educational demo: enter simulated or manually observed measurements.")

    while True:
        print("\n1. Take a battery reading")
        print("2. View the last five readings")
        print("3. View monitoring summary")
        print("4. Make a graph")
        print("5. Analyze battery data")
        print("6. Exit")

        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            take_reading()
        elif choice == "2":
            show_history()
        elif choice == "3":
            show_summary()
        elif choice == "4":
            make_chart()
        elif choice == "5":
            analyze_readings()
        elif choice == "6":
            print("Battery Monitoring Stopped")
            break
        else:
            print("Please enter a number from 1 to 6.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nBattery Monitoring Stopped")