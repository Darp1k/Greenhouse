import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:password@127.0.0.1:3306/greenhouse_db"
)

#create engine with pool_pre_ping=True to ensure that the connection is alive before using it
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# the master class that all models will inherit from. This is a SQLAlchemy convention.
Base = declarative_base()



class Plant(Base):
    """
    Tracks the physical identity and location of each pea plant.
    """
    __tablename__ = "plants"

    plant_id = Column(String(50), primary_key=True, index=True)
    row_number = Column(Integer)
    position_index = Column(Integer)
    planted_date = Column(Date)
    status = Column(String(20), default="active") # e.g. "active", "harvested"

    observations = relationship("Observation", back_populates="plant")


class DroneFlight(Base):
    """
    Records metadata about a specific data collection run.
    """
    __tablename__ = "drone_flights"

    flight_id = Column(String(50), primary_key=True, index=True)
    flight_timestamp = Column(DateTime, default=datetime.utcnow)
    operator = Column(String(50))
    notes = Column(String(255))

    observations = relationship("Observation", back_populates="flight")


class Observation(Base):
    """
    The core tracking table where the computer vision pipeline dumps its data.
    """
    __tablename__ = "observations"

    observation_id = Column(String(50), primary_key=True, index=True)
    
    plant_id = Column(String(50), ForeignKey("plants.plant_id"), index=True)
    flight_id = Column(String(50), ForeignKey("drone_flights.flight_id"), index=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    node_count = Column(Integer)
    leaf_count = Column(Integer)
    flower_present = Column(Boolean)
    
    image_path = Column(String(255), nullable=True)
    confidence_score = Column(Float, nullable=True)

    plant = relationship("Plant", back_populates="observations")
    flight = relationship("DroneFlight", back_populates="observations")


#INITIALIZE DATABASE SCHEMA
Base.metadata.create_all(bind=engine)