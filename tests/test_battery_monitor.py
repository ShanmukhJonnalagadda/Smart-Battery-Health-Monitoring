
import unittest

from battery_monitor import (
    voltage_status,
    temperature_status,
    battery_status
)


class TestBatteryMonitoring(unittest.TestCase):

    # Voltage tests

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

    # Temperature tests

    def test_low_temperature(self):
        self.assertEqual(temperature_status(10), "Too Cold")

    def test_normal_temperature(self):
        self.assertEqual(temperature_status(30), "Normal")

    def test_high_temperature(self):
        self.assertEqual(temperature_status(45), "High")

    def test_temperature_boundaries(self):
        self.assertEqual(temperature_status(15), "Normal")
        self.assertEqual(temperature_status(40), "Normal")

    # Overall battery health tests

    def test_healthy_battery(self):
        self.assertEqual(
            battery_status(3.8, 30), "HEALTHY"
        )

    def test_warning_battery(self):
        self.assertEqual(
            battery_status(3.8, 45), "WARNING"
        )

    def test_critical_low_voltage(self):
        self.assertEqual(
            battery_status(2.9, 30), "CRITICAL"
        )

    def test_critical_high_temperature(self):
        self.assertEqual(
            battery_status(3.8, 55), "CRITICAL"
        )


if __name__ == "__main__":
    unittest.main()

