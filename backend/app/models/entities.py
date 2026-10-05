import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    preferences = relationship("Preference", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")


class Preference(Base):
    __tablename__ = "preferences"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Quality Weights (0-100 or 0.0-1.0)
    relevance_weight = Column(Float, default=0.25)
    correctness_weight = Column(Float, default=0.25)
    completeness_weight = Column(Float, default=0.15)
    clarity_weight = Column(Float, default=0.15)
    consistency_weight = Column(Float, default=0.05)
    preference_match_weight = Column(Float, default=0.10)
    conciseness_weight = Column(Float, default=0.05)
    technical_depth_weight = Column(Float, default=0.0)
    creativity_weight = Column(Float, default=0.0)
    
    # Resource Penalty Weights
    cost_weight = Column(Float, default=0.0)
    token_weight = Column(Float, default=0.0)
    latency_weight = Column(Float, default=0.0)
    
    # Resource Limits
    max_cost = Column(Float, default=0.10)
    max_tokens = Column(Integer, default=4000)
    max_latency_ms = Column(Integer, default=15000)
    
    scoring_mode = Column(String(50), default="quality-first")  # quality-first, balanced, cost-aware, user-customized
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="preferences")


class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), nullable=True)  # educational, coding, reasoning, creative, factoid
    domain = Column(String(50), nullable=True)      # computer_science, mathematics, general, etc.
    difficulty = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    expected_style = Column(String(50), nullable=True)
    recommended_criteria = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="queries")
    model_runs = relationship("ModelRun", back_populates="query", cascade="all, delete-orphan")
    conflicts = relationship("Conflict", back_populates="query", cascade="all, delete-orphan")
    synthesis_runs = relationship("SynthesisRun", back_populates="query", cascade="all, delete-orphan")


class ModelRun(Base):
    __tablename__ = "model_runs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    model = Column(String(150), nullable=False)
    provider = Column(String(100), nullable=True)
    response_text = Column(Text, nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    status = Column(String(50), default="success")  # success, error, timeout
    generation_id = Column(String(150), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    query = relationship("Query", back_populates="model_runs")
    evaluations = relationship("Evaluation", back_populates="model_run", cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_run_id = Column(Integer, ForeignKey("model_runs.id"), nullable=False)
    evaluator_model = Column(String(150), nullable=False)
    
    relevance = Column(Float, default=0.0)
    correctness = Column(Float, default=0.0)
    completeness = Column(Float, default=0.0)
    clarity = Column(Float, default=0.0)
    consistency = Column(Float, default=0.0)
    preference_match = Column(Float, default=0.0)
    conciseness = Column(Float, default=0.0)
    technical_depth = Column(Float, default=0.0)
    
    overall_score = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    model_run = relationship("ModelRun", back_populates="evaluations")


class Conflict(Base):
    __tablename__ = "conflicts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    topic = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), default="medium")  # low, medium, high
    supporting_responses = Column(JSON, nullable=True)
    agreement_points = Column(JSON, nullable=True)
    conflict_points = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    query = relationship("Query", back_populates="conflicts")


class SynthesisRun(Base):
    __tablename__ = "synthesis_runs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    synthesis_model = Column(String(150), nullable=False)
    context = Column(Text, nullable=True)
    final_response = Column(Text, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    status = Column(String(50), default="success")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    query = relationship("Query", back_populates="synthesis_runs")
    final_evaluation = relationship("FinalEvaluation", uselist=False, back_populates="synthesis_run", cascade="all, delete-orphan")


class FinalEvaluation(Base):
    __tablename__ = "final_evaluations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    synthesis_run_id = Column(Integer, ForeignKey("synthesis_runs.id"), nullable=False)
    evaluator_model = Column(String(150), nullable=False)
    
    relevance = Column(Float, default=0.0)
    correctness = Column(Float, default=0.0)
    completeness = Column(Float, default=0.0)
    clarity = Column(Float, default=0.0)
    consistency = Column(Float, default=0.0)
    preference_match = Column(Float, default=0.0)
    conciseness = Column(Float, default=0.0)
    technical_depth = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=True)
    
    best_candidate_model = Column(String(150), nullable=True)
    best_candidate_score = Column(Float, default=0.0)
    improvement_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    synthesis_run = relationship("SynthesisRun", back_populates="final_evaluation")


class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    configuration = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    query_id = Column(Integer, nullable=True)
    method = Column(String(100), nullable=False)  # baseline_1_single, baseline_2_best_selection, baseline_3_simple_synthesis, baseline_4_eval_guided, proposed_system
    quality_score = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    tokens = Column(Integer, default=0)
    latency = Column(Float, default=0.0)
    human_score = Column(Float, nullable=True)
    metrics_breakdown = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    experiment = relationship("Experiment", back_populates="results")


class HumanEvaluation(Base):
    __tablename__ = "human_evaluations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    candidate_a_id = Column(Integer, nullable=True)
    candidate_b_id = Column(Integer, nullable=True)
    preferred_choice = Column(String(50), nullable=False)  # 'A', 'B', 'equal'
    relevance_score = Column(Integer, default=5)           # 1-5
    correctness_score = Column(Integer, default=5)
    clarity_score = Column(Integer, default=5)
    completeness_score = Column(Integer, default=5)
    preference_match_score = Column(Integer, default=5)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
