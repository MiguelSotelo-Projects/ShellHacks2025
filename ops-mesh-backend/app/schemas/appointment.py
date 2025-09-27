from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True)
    confirmation_code = Column(String, unique=True, index=True)
    patient_name = Column(String)
    appointment_time = Column(DateTime)
    department = Column(String)
    provider = Column(String)
    status = Column(String, default="confirmed")