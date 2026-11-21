from datetime import date
from typing import Literal
from pydantic import Field, model_validator
from app.schemas.auth import StrictModel

# Physical bounds, not agronomic reference ranges. Lab method is retained verbatim.
PARAMETERS = {
    'nitrogen': (0, 100000, ['mg/kg', 'kg/ha', '%']),
    'phosphorus': (0, 100000, ['mg/kg', 'kg/ha']),
    'potassium': (0, 100000, ['mg/kg', 'kg/ha']),
    'ph': (0, 14, ['pH']),
    'ec': (0, 100, ['dS/m', 'mS/cm']),
    'organic_carbon': (0, 100, ['%', 'g/kg']),
    'organic_matter': (0, 100, ['%']),
    'moisture': (0, 100, ['%']),
    'temperature': (0, 80, ['°C']),
    **{k: (0, 100000, ['mg/kg']) for k in ['sulphur', 'zinc', 'iron', 'boron', 'copper', 'manganese', 'calcium', 'magnesium']},
}


class FarmInput(StrictModel):
    name: str = Field(min_length=2, max_length=150)
    state: str = Field(min_length=2, max_length=100)
    district: str = Field(min_length=2, max_length=100)
    village: str = Field(default='', max_length=100)
    location: str = Field(default='', max_length=250)
    survey_number: str = Field(default='', max_length=100)
    area: float = Field(gt=0, le=1000000, allow_inf_nan=False)
    area_unit: Literal['acre', 'hectare', 'cent', 'm²'] = 'acre'


class FieldInput(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    area: float = Field(gt=0, le=1000000, allow_inf_nan=False)
    soil_type: str = Field(default='', max_length=100)


class MeasurementInput(StrictModel):
    parameter: str
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=30)
    method: str = Field(min_length=2, max_length=150)

    @model_validator(mode='after')
    def check_measurement(self):
        if self.parameter not in PARAMETERS:
            raise ValueError('Unknown soil parameter')
        low, high, units = PARAMETERS[self.parameter]
        if self.unit not in units:
            raise ValueError(f'{self.parameter}: supported units are {", ".join(units)}')
        if not low <= self.value <= high:
            raise ValueError(f'{self.parameter}: value must be between {low} and {high}')
        if self.unit == '%' and self.value > 100:
            raise ValueError('Percentage cannot exceed 100')
        return self


class ClimateInput(StrictModel):
    temperature: float | None = Field(default=None, ge=-20, le=60, allow_inf_nan=False)
    humidity: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    rainfall: float | None = Field(default=None, ge=0, le=15000, allow_inf_nan=False)
    rainfall_period: Literal['annual', 'seasonal', 'monthly'] | None = None
    season: str = Field(default='', max_length=80)
    irrigation: Literal['rainfed', 'available', 'limited', 'unknown'] = 'unknown'
    growth_stage: str = Field(default='', max_length=100)


class SampleInput(StrictModel):
    farm_id: str
    field_id: str | None = None
    sample_code: str = Field(min_length=1, max_length=100)
    collected_on: date
    location: str = Field(default='', max_length=250)
    laboratory: str = Field(default='', max_length=200)
    status: Literal['draft', 'submitted'] = 'submitted'
    climate: ClimateInput = Field(default_factory=ClimateInput)
    measurements: list[MeasurementInput] = Field(default_factory=list, max_length=17)

    @model_validator(mode='after')
    def check_sample(self):
        names = [m.parameter for m in self.measurements]
        if len(names) != len(set(names)):
            raise ValueError('Each parameter may occur only once')
        if self.collected_on > date.today():
            raise ValueError('Collection date cannot be in the future')
        if self.status == 'submitted' and not {'nitrogen','phosphorus','potassium','ph','ec','organic_carbon','organic_matter','moisture','temperature'}.issubset(names):
            raise ValueError('Submitted samples require all nine primary soil parameters; save a draft to continue later')
        return self
