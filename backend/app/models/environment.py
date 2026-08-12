"""Environment reading data model."""

from pydantic import BaseModel, Field
from typing import Optional


class EnvironmentReading(BaseModel):
    """DHT22 sensor data point."""
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity in percentage")
    fan_on: bool = Field(False, description="Whether cooling fan is currently commanded on")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of reading")
