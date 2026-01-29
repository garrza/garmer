"""Stress data models for Garmin stress monitoring."""

from datetime import datetime
from typing import Any

from pydantic import Field

from garmer.models.base import GarminBaseModel, parse_garmin_timestamp


class StressSample(GarminBaseModel):
    """A single stress measurement sample."""

    timestamp: datetime | None = None
    stress_level: int = Field(default=-1)  # -1 indicates no measurement

    @classmethod
    def from_garmin_response(cls, data: dict[str, Any]) -> "StressSample":
        """Parse stress sample from Garmin response."""
        return cls(
            timestamp=parse_garmin_timestamp(data.get("timestamp")),
            stress_level=data.get("stressLevel", -1),
        )

    @property
    def is_valid(self) -> bool:
        """Check if this is a valid stress measurement."""
        return self.stress_level >= 0

    @property
    def stress_category(self) -> str:
        """Get stress level category."""
        if self.stress_level < 0:
            return "unmeasured"
        elif self.stress_level <= 25:
            return "rest"
        elif self.stress_level <= 50:
            return "low"
        elif self.stress_level <= 75:
            return "medium"
        else:
            return "high"


class StressData(GarminBaseModel):
    """Stress data for a specific day."""

    # Date info
    calendar_date: str | None = Field(alias="calendarDate", default=None)
    start_timestamp: datetime | None = Field(alias="startTimestampGMT", default=None)
    end_timestamp: datetime | None = Field(alias="endTimestampGMT", default=None)

    # Summary statistics
    overall_stress_level: int | None = Field(alias="overallStressLevel", default=None)
    avg_stress_level: int | None = Field(alias="avgStressLevel", default=None)
    max_stress_level: int | None = Field(alias="maxStressLevel", default=None)

    # Time in different stress states (in seconds)
    rest_stress_duration: int = Field(alias="restStressDuration", default=0)
    low_stress_duration: int = Field(alias="lowStressDuration", default=0)
    medium_stress_duration: int = Field(alias="mediumStressDuration", default=0)
    high_stress_duration: int = Field(alias="highStressDuration", default=0)

    # Activity duration
    activity_stress_duration: int = Field(alias="activityStressDuration", default=0)
    uncategorized_stress_duration: int = Field(
        alias="uncategorizedStressDuration", default=0
    )

    # Body battery correlation
    body_battery_charged: int | None = Field(alias="bodyBatteryCharged", default=None)
    body_battery_drained: int | None = Field(alias="bodyBatteryDrained", default=None)

    # Stress samples throughout the day
    stress_samples: list[StressSample] = Field(
        alias="stressValuesArray", default_factory=list
    )

    # Raw data
    raw_data: dict[str, Any] | None = Field(default=None, exclude=True)

    @classmethod
    def from_garmin_response(cls, data: dict[str, Any]) -> "StressData":
        """Parse stress data from Garmin API response."""
        # Parse stress samples
        samples = []
        raw_samples = data.get("stressValuesArray", [])
        if raw_samples:
            for sample in raw_samples:
                if isinstance(sample, list) and len(sample) >= 2:
                    samples.append(
                        StressSample(
                            timestamp=parse_garmin_timestamp(sample[0]),
                            stress_level=sample[1] if sample[1] is not None else -1,
                        )
                    )
                elif isinstance(sample, dict):
                    samples.append(StressSample.from_garmin_response(sample))

        return cls(
            calendar_date=data.get("calendarDate"),
            start_timestamp=parse_garmin_timestamp(data.get("startTimestampGMT")),
            end_timestamp=parse_garmin_timestamp(data.get("endTimestampGMT")),
            overall_stress_level=data.get("overallStressLevel"),
            avg_stress_level=data.get("avgStressLevel"),
            max_stress_level=data.get("maxStressLevel"),
            rest_stress_duration=data.get("restStressDuration", 0),
            low_stress_duration=data.get("lowStressDuration", 0),
            medium_stress_duration=data.get("mediumStressDuration", 0),
            high_stress_duration=data.get("highStressDuration", 0),
            activity_stress_duration=data.get("activityStressDuration", 0),
            uncategorized_stress_duration=data.get("uncategorizedStressDuration", 0),
            body_battery_charged=data.get("bodyBatteryChargedValue"),
            body_battery_drained=data.get("bodyBatteryDrainedValue"),
            stress_samples=samples,
            raw_data=data,
        )

    @property
    def rest_duration_hours(self) -> float:
        """Get rest duration in hours."""
        return self.rest_stress_duration / 3600.0

    @property
    def low_stress_hours(self) -> float:
        """Get low stress duration in hours."""
        return self.low_stress_duration / 3600.0

    @property
    def medium_stress_hours(self) -> float:
        """Get medium stress duration in hours."""
        return self.medium_stress_duration / 3600.0

    @property
    def high_stress_hours(self) -> float:
        """Get high stress duration in hours."""
        return self.high_stress_duration / 3600.0

    @property
    def total_measured_duration_hours(self) -> float:
        """Get total measured stress duration in hours."""
        total_seconds = (
            self.rest_stress_duration
            + self.low_stress_duration
            + self.medium_stress_duration
            + self.high_stress_duration
        )
        return total_seconds / 3600.0

    def get_valid_samples(self) -> list[StressSample]:
        """Get only valid stress measurements."""
        return [s for s in self.stress_samples if s.is_valid]
