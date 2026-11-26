"""Automated tests for the Smart Battery Health Monitoring System."""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import csv
import tempfile
from pathlib import Path
import battery_monitor as bm

from battery_monitor import (
    voltage_status,
    temperature_status,
    battery_status,
    analyze_readings,
)


class TestBatteryMonitoring(unittest.TestCase):
    # Original voltage tests
    def test_low_voltage(self):
        self.assertEqual(voltage_status(3.1), "Low")

    def test_normal_voltage(self):
        self.assertEqual(voltage_status(3.8), "Normal")

    def test_high_voltage(self):
        self.assertEqual(voltage_status(4.5), "High")

    def test_voltage_lower_boundary(self):
        self.assertEqual(voltage_status(3.2), "Normal")

    def test_voltage_upper_boundary(self):
        self.assertEqual(voltage_status(4.2), "Normal")

    # Original temperature tests
    def test_low_temperature(self):
        self.assertEqual(temperature_status(10), "Too Cold")

    def test_normal_temperature(self):
        self.assertEqual(temperature_status(30), "Normal")

    def test_high_temperature(self):
        self.assertEqual(temperature_status(45), "High")

    def test_temperature_boundaries(self):
        self.assertEqual(temperature_status(15), "Normal")
        self.assertEqual(temperature_status(40), "Normal")

    # Original overall-health tests
    def test_healthy_battery(self):
        self.assertEqual(battery_status(3.8, 30), "HEALTHY")

    def test_warning_battery(self):
        self.assertEqual(battery_status(3.8, 45), "WARNING")

    def test_critical_low_voltage(self):
        self.assertEqual(battery_status(2.9, 30), "CRITICAL")

    def test_critical_high_temperature(self):
        self.assertEqual(battery_status(3.8, 55), "CRITICAL")

    # New tests for the analysis feature
    @patch("battery_monitor.load_readings")
    def test_analyze_readings_with_data(self, mock_load_readings):
        # Mock data: 2 of the 4 saved readings are HEALTHY.
        mock_load_readings.return_value = [
            {"voltage_v": "3.67", "temperature_c": "30", "battery_status": "HEALTHY"},
            {"voltage_v": "4.36", "temperature_c": "35", "battery_status": "WARNING"},
            {"voltage_v": "3.80", "temperature_c": "42", "battery_status": "WARNING"},
            {"voltage_v": "4.00", "temperature_c": "28", "battery_status": "HEALTHY"},
        ]
        output = StringIO()
        # The analysis should return directly, never start another menu.
        with patch("builtins.input", side_effect=AssertionError("Analysis unexpectedly requested input")):
            with redirect_stdout(output):
                analyze_readings()

        result = output.getvalue()
        self.assertIn("Total readings: 4", result)
        self.assertIn("Lowest voltage: 3.67 V", result)
        self.assertIn("Highest voltage: 4.36 V", result)
        self.assertIn("Highest temperature: 42.00 C", result)
        self.assertIn("Healthy readings: 50.0%", result)

    @patch("battery_monitor.load_readings", return_value=[])
    def test_analyze_readings_no_data(self, mock_load_readings):
        output = StringIO()
        with redirect_stdout(output):
            analyze_readings()
        self.assertIn("No battery readings available.", output.getvalue())
        mock_load_readings.assert_called_once_with()


class TestExtendedBatteryMonitoring(unittest.TestCase):

    def setUp(self):
        # Use temporary storage to protect existing battery readings.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.data_file = (
            Path(self.temp_dir.name) / "battery_readings.csv"
        )

        self.data_patch = patch.object(
            bm, "DATA_FILE", self.data_file
        )

        self.data_patch.start()
        self.addCleanup(self.data_patch.stop)

    def create_reading(self):
        return {
            "timestamp": "2026-11-24T10:00:00-05:00",
            "battery_id": "101",
            "voltage_v": "3.856",
            "current_a": "1.2",
            "temperature_c": "30",
            "power_w": "4.6272",
            "voltage_status": "Normal",
            "temperature_status": "Normal",
            "battery_status": "HEALTHY",
        }

    # ==========================================
    # SAMPLE DATASET IMPORT
    # ==========================================

    def test_sample_dataset_import(self):
        with redirect_stdout(StringIO()):
            bm.load_sample_data()

        readings = bm.load_readings()

        self.assertEqual(len(readings), 18)

        battery_ids = {
            row["battery_id"] for row in readings
        }

        self.assertEqual(
            battery_ids, {"101", "102", "103"}
        )

    def test_missing_sample_dataset(self):
        missing_file = (
            Path(self.temp_dir.name) / "missing.csv"
        )

        output = StringIO()

        with patch.object(bm, "SAMPLE_FILE", missing_file):
            with redirect_stdout(output):
                bm.load_sample_data()

        self.assertIn(
            "Sample dataset not found.",
            output.getvalue()
        )

        self.assertFalse(self.data_file.exists())

    # ==========================================
    # DUPLICATE IMPORT PREVENTION
    # ==========================================

    def test_duplicate_sample_import(self):
        with redirect_stdout(StringIO()):
            bm.load_sample_data()
            bm.load_sample_data()

        self.assertEqual(len(bm.load_readings()), 18)

    def test_existing_reading_preserved(self):
        reading = self.create_reading()

        bm.save_reading(reading)

        with redirect_stdout(StringIO()):
            bm.load_sample_data()

        readings = bm.load_readings()

        self.assertEqual(len(readings), 18)
        self.assertEqual(readings[0], reading)

    # ==========================================
    # INDIVIDUAL BATTERY ANALYSIS
    # ==========================================

    def test_individual_battery_analysis(self):
        with redirect_stdout(StringIO()):
            bm.load_sample_data()

        output = StringIO()

        with patch("builtins.input", return_value="101"):
            with redirect_stdout(output):
                bm.analyze_individual_battery()

        result = output.getvalue()

        self.assertIn("Battery 101 Analysis", result)
        self.assertIn("Total readings: 6", result)
        self.assertIn("Lowest voltage: 2.90 V", result)
        self.assertIn("Highest voltage: 4.10 V", result)
        self.assertIn("Highest temperature: 52.00 C", result)
        self.assertIn("HEALTHY: 4", result)
        self.assertIn("WARNING: 1", result)
        self.assertIn("CRITICAL: 1", result)
        self.assertIn("Healthy readings: 66.7%", result)

    def test_unknown_battery_id(self):
        with redirect_stdout(StringIO()):
            bm.load_sample_data()

        output = StringIO()

        with patch("builtins.input", return_value="999"):
            with redirect_stdout(output):
                bm.analyze_individual_battery()

        self.assertIn(
            "Battery ID not found.",
            output.getvalue()
        )

    def test_individual_analysis_no_data(self):
        output = StringIO()

        with redirect_stdout(output):
            bm.analyze_individual_battery()

        self.assertIn(
            "No battery readings available.",
            output.getvalue()
        )

    # ==========================================
    # CSV DATA PERSISTENCE
    # ==========================================

    def test_save_and_load_reading(self):
        reading = self.create_reading()

        bm.save_reading(reading)

        self.assertEqual(
            bm.load_readings(), [reading]
        )

    def test_csv_header_written_once(self):
        reading = self.create_reading()

        bm.save_reading(reading)
        bm.save_reading(reading)

        with self.data_file.open(
            "r", newline="", encoding="utf-8"
        ) as file:

            rows = list(csv.reader(file))

        self.assertEqual(rows[0], bm.COLUMNS)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows.count(bm.COLUMNS), 1)

    def test_measurement_precision(self):
        with patch(
            "builtins.input",
            side_effect=["101", "3.856", "1.234", "30.125"]
        ):
            with redirect_stdout(StringIO()):
                bm.take_reading()

        reading = bm.load_readings()[0]

        self.assertEqual(
            float(reading["voltage_v"]), 3.856
        )

        self.assertEqual(
            float(reading["current_a"]), 1.234
        )

        self.assertEqual(
            float(reading["temperature_c"]), 30.125
        )

        self.assertAlmostEqual(
            float(reading["power_w"]),
            3.856 * 1.234
        )

    # ==========================================
    # INPUT VALIDATION
    # ==========================================

    def test_invalid_text_input(self):
        with patch(
            "builtins.input",
            side_effect=["abc", "3.8"]
        ):
            with redirect_stdout(StringIO()):
                result = bm.get_number("Voltage: ")

        self.assertEqual(result, 3.8)

    def test_non_finite_input(self):
        with patch(
            "builtins.input",
            side_effect=["nan", "inf", "-inf", "3.8"]
        ):
            with redirect_stdout(StringIO()):
                result = bm.get_number("Voltage: ")

        self.assertEqual(result, 3.8)

    def test_negative_voltage_rejected(self):
        with patch(
            "builtins.input",
            side_effect=["-2", "3.8"]
        ):
            with redirect_stdout(StringIO()):
                result = bm.get_number("Voltage: ")

        self.assertEqual(result, 3.8)

    # ==========================================
    # CRITICAL BOUNDARY CONDITIONS
    # ==========================================

    def test_critical_voltage_boundary(self):
        self.assertEqual(
            bm.battery_status(3.0, 30), "WARNING"
        )

        self.assertEqual(
            bm.battery_status(2.999, 30), "CRITICAL"
        )

    def test_critical_temperature_boundary(self):
        self.assertEqual(
            bm.battery_status(3.8, 50), "WARNING"
        )

        self.assertEqual(
            bm.battery_status(3.8, 50.001), "CRITICAL"
        )




if __name__ == "__main__":
    unittest.main()
