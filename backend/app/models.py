from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model for customers and operators"""
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    consent_status = Column(Boolean, default=False)
    consent_granted_at = Column(DateTime, nullable=True)
    consent_revoked_at = Column(DateTime, nullable=True)
    user_type = Column(String, CheckConstraint("user_type IN ('customer', 'operator')"), default='customer')

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="user", cascade="all, delete-orphan")
    user_features = relationship("UserFeature", back_populates="user", cascade="all, delete-orphan")
    personas = relationship("Persona", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    consent_logs = relationship("ConsentLog", back_populates="user", cascade="all, delete-orphan")
    operator_actions = relationship("OperatorAction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}', user_type='{self.user_type}')>"


class Account(Base):
    """Account model for bank accounts, credit cards, and investment accounts"""
    __tablename__ = "accounts"

    account_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    type = Column(String, nullable=False)
    subtype = Column(String, nullable=True)
    balance_available = Column(Float, nullable=True)
    balance_current = Column(Float, nullable=True)
    balance_limit = Column(Float, nullable=True)
    iso_currency_code = Column(String, default='USD')
    holder_category = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account(account_id='{self.account_id}', user_id='{self.user_id}', type='{self.type}')>"


class Transaction(Base):
    """Transaction model for all financial transactions"""
    __tablename__ = "transactions"

    transaction_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    merchant_name = Column(String, nullable=True)
    merchant_entity_id = Column(String, nullable=True)
    payment_channel = Column(String, nullable=True)
    category_primary = Column(String, nullable=True)
    category_detailed = Column(String, nullable=True)
    pending = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")

    # Indexes
    __table_args__ = (
        Index('idx_transactions_user_date', 'user_id', 'date'),
        Index('idx_transactions_merchant', 'merchant_name'),
    )

    def __repr__(self):
        return f"<Transaction(transaction_id='{self.transaction_id}', user_id='{self.user_id}', amount={self.amount}, date='{self.date}')>"


class Liability(Base):
    """Liability model for credit cards and loans"""
    __tablename__ = "liabilities"

    liability_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    liability_type = Column(String, CheckConstraint("liability_type IN ('credit_card', 'loan', 'mortgage', 'other')"), nullable=False)
    apr_purchase = Column(Float, nullable=True)
    apr_balance_transfer = Column(Float, nullable=True)
    apr_cash_advance = Column(Float, nullable=True)
    minimum_payment_amount = Column(Float, nullable=True)
    last_payment_amount = Column(Float, nullable=True)
    is_overdue = Column(Boolean, default=False)
    next_payment_due_date = Column(Date, nullable=True)
    last_statement_balance = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="liabilities")
    account = relationship("Account", back_populates="liabilities")

    def __repr__(self):
        return f"<Liability(liability_id='{self.liability_id}', user_id='{self.user_id}', liability_type='{self.liability_type}')>"


class UserFeature(Base):
    """User features model for computed behavioral signals"""
    __tablename__ = "user_features"

    feature_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    window_days = Column(Integer, nullable=False)  # 30 or 180
    computed_at = Column(DateTime, default=func.now())

    # Subscription signals
    recurring_merchants = Column(Integer, default=0)
    monthly_recurring_spend = Column(Float, default=0)
    subscription_spend_share = Column(Float, default=0)

    # Savings signals
    net_savings_inflow = Column(Float, default=0)
    savings_growth_rate = Column(Float, default=0)
    emergency_fund_months = Column(Float, default=0)

    # Credit signals
    avg_utilization = Column(Float, default=0)
    max_utilization = Column(Float, default=0)
    utilization_30_flag = Column(Boolean, default=False)
    utilization_50_flag = Column(Boolean, default=False)
    utilization_80_flag = Column(Boolean, default=False)
    minimum_payment_only_flag = Column(Boolean, default=False)
    interest_charges_present = Column(Boolean, default=False)
    any_overdue = Column(Boolean, default=False)

    # Income signals
    payroll_detected = Column(Boolean, default=False)
    median_pay_gap_days = Column(Integer, nullable=True)
    income_variability = Column(Float, nullable=True)
    cash_flow_buffer_months = Column(Float, default=0)
    avg_monthly_income = Column(Float, default=0)

    # Investment signals
    investment_account_detected = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="user_features")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'window_days', name='uq_user_features_user_window'),
        Index('idx_features_user', 'user_id'),
    )

    def __repr__(self):
        return f"<UserFeature(feature_id={self.feature_id}, user_id='{self.user_id}', window_days={self.window_days})>"


class Persona(Base):
    """Persona model for user persona assignments"""
    __tablename__ = "personas"

    persona_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    window_days = Column(Integer, nullable=False)
    persona_type = Column(String, CheckConstraint("persona_type IN ('high_utilization', 'variable_income', 'subscription_heavy', 'savings_builder', 'wealth_builder')"), nullable=False)
    confidence_score = Column(Float, default=1.0)
    assigned_at = Column(DateTime, default=func.now())
    reasoning = Column(Text, nullable=True)  # JSON with matched criteria

    # Relationships
    user = relationship("User", back_populates="personas")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'window_days', name='uq_personas_user_window'),
        Index('idx_personas_user', 'user_id'),
    )

    def __repr__(self):
        return f"<Persona(persona_id={self.persona_id}, user_id='{self.user_id}', persona_type='{self.persona_type}', window_days={self.window_days})>"


class Recommendation(Base):
    """Recommendation model for AI-generated content"""
    __tablename__ = "recommendations"

    recommendation_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    persona_type = Column(String, nullable=False)
    window_days = Column(Integer, nullable=False)
    content_type = Column(String, CheckConstraint("content_type IN ('education', 'partner_offer')"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    status = Column(String, CheckConstraint("status IN ('pending_approval', 'approved', 'overridden', 'rejected')"), default='pending_approval')
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    override_reason = Column(Text, nullable=True)
    original_content = Column(Text, nullable=True)  # JSON
    metadata_json = Column(Text, nullable=True)  # JSON (renamed from metadata to avoid SQLAlchemy conflict)
    generated_at = Column(DateTime, default=func.now())
    generation_time_ms = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="recommendations")
    operator_actions = relationship("OperatorAction", back_populates="recommendation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_recommendations_user', 'user_id'),
        Index('idx_recommendations_status', 'status'),
    )

    def __repr__(self):
        return f"<Recommendation(recommendation_id='{self.recommendation_id}', user_id='{self.user_id}', status='{self.status}')>"


class EvaluationMetric(Base):
    """Evaluation metrics model for system performance tracking"""
    __tablename__ = "evaluation_metrics"

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    total_users = Column(Integer, nullable=True)
    users_with_persona = Column(Integer, nullable=True)
    users_with_behaviors = Column(Integer, nullable=True)
    coverage_percentage = Column(Float, nullable=True)
    total_recommendations = Column(Integer, nullable=True)
    recommendations_with_rationale = Column(Integer, nullable=True)
    explainability_percentage = Column(Float, nullable=True)
    avg_recommendation_latency_ms = Column(Float, nullable=True)
    p95_recommendation_latency_ms = Column(Float, nullable=True)
    recommendations_with_traces = Column(Integer, nullable=True)
    auditability_percentage = Column(Float, nullable=True)
    details = Column(Text, nullable=True)  # JSON

    def __repr__(self):
        return f"<EvaluationMetric(metric_id={self.metric_id}, run_id='{self.run_id}', timestamp='{self.timestamp}')>"


class ConsentLog(Base):
    """Consent log model for audit trail of consent changes"""
    __tablename__ = "consent_log"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    action = Column(String, CheckConstraint("action IN ('granted', 'revoked')"), nullable=False)
    timestamp = Column(DateTime, default=func.now())
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="consent_logs")

    # Indexes
    __table_args__ = (
        Index('idx_consent_log_user', 'user_id'),
    )

    def __repr__(self):
        return f"<ConsentLog(log_id={self.log_id}, user_id='{self.user_id}', action='{self.action}')>"


class OperatorAction(Base):
    """Operator action model for approve/reject/override logging"""
    __tablename__ = "operator_actions"

    action_id = Column(Integer, primary_key=True, autoincrement=True)
    operator_id = Column(String, nullable=False)
    action_type = Column(String, CheckConstraint("action_type IN ('approve', 'reject', 'override')"), nullable=False)
    recommendation_id = Column(String, ForeignKey("recommendations.recommendation_id"), nullable=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())

    # Relationships
    user = relationship("User", back_populates="operator_actions")
    recommendation = relationship("Recommendation", back_populates="operator_actions")

    def __repr__(self):
        return f"<OperatorAction(action_id={self.action_id}, operator_id='{self.operator_id}', action_type='{self.action_type}')>"
