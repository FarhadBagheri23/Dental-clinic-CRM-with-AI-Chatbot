from datetime import datetime

from pydantic import BaseModel


class PageMeta(BaseModel):
    total: int
    page: int
    pages: int
    size: int


class Patient(BaseModel):
    patient_id: int
    national_code: str
    first_name: str
    last_name: str
    gender: str | None = None
    phone: str | None = None
    birth_date: datetime | None = None
    registration_date: datetime | None = None
    allergies: str | None = None
    insurance: str | None = None


class Appointment(BaseModel):
    appointment_id: int
    scheduled_datetime: datetime | None = None
    status: str
    chair_number: int | None = None
    patient: str | None = None
    dentist: str | None = None
    specialty: str | None = None


class Invoice(BaseModel):
    invoice_id: int
    issue_date: datetime | None = None
    total_amount: float
    insurance_covered: float
    patient_share: float
    paid: float
    balance: float
    status: str
    patient: str | None = None


class PatientPage(BaseModel):
    rows: list[Patient]
    meta: PageMeta


class AppointmentPage(BaseModel):
    rows: list[Appointment]
    meta: PageMeta


class InvoicePage(BaseModel):
    rows: list[Invoice]
    meta: PageMeta
