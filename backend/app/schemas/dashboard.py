from pydantic import BaseModel


class StatusCount(BaseModel):
    status: str
    n: int


class Counts(BaseModel):
    patients: int
    sessions: int
    dentists: int
    upcoming: int
    appointments: int


class Summary(BaseModel):
    revenue: float
    insurance_covered: float
    patient_share: float
    collected: float
    outstanding: float
    collection_rate: int
    counts: Counts
    appointment_status: list[StatusCount]
    invoice_status: list[StatusCount]


class MonthlyRevenue(BaseModel):
    month: str  # YYYY-MM
    revenue: float
    collected: float


class DentistPerformance(BaseModel):
    name: str
    specialty: str
    revenue: float
    sessions: int


class ServiceRevenue(BaseModel):
    name: str
    category: str
    n: int
    revenue: float


class ConsumableStock(BaseModel):
    consumable_id: int
    name: str
    unit: str
    stock_quantity: float
    min_stock_level: float
    unit_price: float
    supplier: str | None = None
    critical: bool
