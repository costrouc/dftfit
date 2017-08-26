from contextlib import contextmanager

from sqlalchemy import create_engine, types
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


class DatabaseManager:
    def __init__(self, filename=None):
        filename = filename or ':memory'
        self.engine = create_engine('sqlite:///{}'.format(filename))
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self, base):
        base.metadata.create_all(self.engine)

    @contextmanager
    def transaction(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


Base = declarative_base()


class Potential(Base):
    __tablename__ = "potential"

    id = Column(types.String, primary_key=True)
    schema = Column(types.String)

    runs = relationship('Run', back_populates='potential')
    evaluations = relationship('Evaluation', back_populates='potential')


class Run(Base):
    __tablename__ = "run"

    id = Column(types.Integer, primary_key=True)

    potential_id = Column(types.Integer, ForeignKey('potential.id'), nullable=False)
    # Calculations
    start_time = Column(types.DateTime)
    end_time = Column(types.DateTime)
    initial_parameters = Column(types.String)
    indicies = Column(types.String)
    bounds = Column(types.String)

    potential = relationship('Potential', back_populates='runs', uselist=False)
    evaluations = relationship('Evaluation', back_populates='run')


class Evaluation(Base):
    __tablename__ = 'evaluation'

    id = Column(types.Integer, primary_key=True)
    potential_id = Column(types.Integer, ForeignKey('potential.id'), nullable=False)
    run_id = Column(types.Integer, ForeignKey('run.id'), nullable=False)

    step = Column(types.Integer)
    parameters = Column(types.String)
    sq_force_error = Column(types.Float)
    sq_stress_error = Column(types.Float)
    sq_energy_error = Column(types.Float)
    weight_forces = Column(types.Float)
    weight_stress = Column(types.Float)
    weight_energy = Column(types.Float)
    score = Column(types.Float)

    potential = relationship('Potential', back_populates='evaluations', uselist=False)
    run = relationship('Run', back_populates='evaluations', uselist=False)
