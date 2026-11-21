"""Automated tests for the Smart Battery Health Monitoring System."""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
