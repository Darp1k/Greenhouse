from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Plant(Base):
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    plant_index = Column(Integer, unique=True, index=True) 
    current_height_cm = Column(Float, default=0.0)
    
    captures = relationship("Capture", back_populates="plant")

class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(String(50), default="Crazyflie_2.1")
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    
    captures = relationship("Capture", back_populates="flight")

class Capture(Base):
    __tablename__ = "captures"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"))
    flight_id = Column(Integer, ForeignKey("flights.id")) # Links to the specific flight
    file_path = Column(String(255), unique=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    plant = relationship("Plant", back_populates="captures")
    flight = relationship("Flight", back_populates="captures")
