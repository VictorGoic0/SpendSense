from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Literal
from datetime import datetime, date


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with core fields"""
    full_name: str
    email: str
    user_type: Literal["customer", "operator"] = Field(default="customer")
    consent_status: bool = Field(default=False)
    consent_granted_at: Optional[datetime] = None
    consent_revoked_at: Optional[datetime] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    user_id: str
    created_at: Optional[datetime] = None


class UserResponse(UserBase):
    """Schema for user response with all fields"""
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Account Schemas
# ============================================================================

class AccountBase(BaseModel):
    """Base account schema with core fields"""
    user_id: str
    type: str
    subtype: Optional[str] = None
    balance_available: Optional[float] = None
    balance_current: Optional[float] = None
    balance_limit: Optional[float] = None
    iso_currency_code: str = Field(default="USD")
    holder_category: Optional[str] = None


class AccountCreate(AccountBase):
    """Schema for creating an account"""
    account_id: str
    created_at: Optional[datetime] = None


class AccountResponse(AccountBase):
    """Schema for account response with all fields"""
    account_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Transaction Schemas
# ============================================================================

class TransactionBase(BaseModel):
    """Base transaction schema with core fields"""
    account_id: str
    user_id: str
    date: date
    amount: float
    merchant_name: Optional[str] = None
    merchant_entity_id: Optional[str] = None
    payment_channel: Optional[str] = None
    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None
    pending: bool = Field(default=False)


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction"""
    transaction_id: str
    created_at: Optional[datetime] = None

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse date from string if needed"""
        if isinstance(v, str):
            return datetime.fromisoformat(v).date()
        return v


class TransactionResponse(TransactionBase):
    """Schema for transaction response with all fields"""
    transaction_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Liability Schemas
# ============================================================================

class LiabilityBase(BaseModel):
    """Base liability schema with core fields"""
    account_id: str
    user_id: str
    liability_type: Literal["credit_card", "loan", "mortgage", "other"]
    apr_purchase: Optional[float] = None
    apr_balance_transfer: Optional[float] = None
    apr_cash_advance: Optional[float] = None
    minimum_payment_amount: Optional[float] = None
    last_payment_amount: Optional[float] = None
    is_overdue: bool = Field(default=False)
    next_payment_due_date: Optional[date] = None
    last_statement_balance: Optional[float] = None
    interest_rate: Optional[float] = None

    @field_validator('next_payment_due_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse date from string if needed"""
        if isinstance(v, str):
            return datetime.fromisoformat(v).date()
        return v


class LiabilityCreate(LiabilityBase):
    """Schema for creating a liability"""
    liability_id: str
    created_at: Optional[datetime] = None


class LiabilityResponse(LiabilityBase):
    """Schema for liability response with all fields"""
    liability_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Ingestion Schemas
# ============================================================================

class IngestRequest(BaseModel):
    """Schema for bulk data ingestion request"""
    users: List[UserCreate] = Field(default_factory=list)
    accounts: List[AccountCreate] = Field(default_factory=list)
    transactions: List[TransactionCreate] = Field(default_factory=list)
    liabilities: List[LiabilityCreate] = Field(default_factory=list)


class IngestResponse(BaseModel):
    """Schema for ingestion response"""
    status: str
    ingested: Dict[str, int]
    duration_ms: int


# ============================================================================
# Feature Schemas
# ============================================================================

class UserFeatureResponse(BaseModel):
    """Schema for user feature response"""
    feature_id: int
    user_id: str
    window_days: int
    computed_at: datetime
    
    # Subscription signals
    recurring_merchants: int = 0
    monthly_recurring_spend: float = 0
    subscription_spend_share: float = 0
    
    # Savings signals
    net_savings_inflow: float = 0
    savings_growth_rate: float = 0
    emergency_fund_months: float = 0
    
    # Credit signals
    avg_utilization: float = 0
    max_utilization: float = 0
    utilization_30_flag: bool = False
    utilization_50_flag: bool = False
    utilization_80_flag: bool = False
    minimum_payment_only_flag: bool = False
    interest_charges_present: bool = False
    any_overdue: bool = False
    
    # Income signals
    payroll_detected: bool = False
    median_pay_gap_days: Optional[int] = None
    income_variability: Optional[float] = None
    cash_flow_buffer_months: float = 0
    avg_monthly_income: float = 0
    
    # Investment signals
    investment_account_detected: bool = False

    class Config:
        from_attributes = True


# ============================================================================
# Persona Schemas
# ============================================================================

class PersonaResponse(BaseModel):
    """Schema for persona response"""
    persona_id: int
    user_id: str
    window_days: int
    persona_type: Literal["high_utilization", "variable_income", "subscription_heavy", "savings_builder", "wealth_builder"]
    confidence_score: float = 1.0
    assigned_at: datetime
    reasoning: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Recommendation Schemas
# ============================================================================

class RecommendationBase(BaseModel):
    """Base recommendation schema with core fields"""
    user_id: str
    persona_type: str
    window_days: int
    content_type: Literal["education", "partner_offer"]
    title: str
    content: str
    rationale: str


class RecommendationCreate(RecommendationBase):
    """Schema for creating a recommendation"""
    recommendation_id: str
    status: Literal["pending_approval", "approved", "overridden", "rejected"] = Field(default="pending_approval")
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    override_reason: Optional[str] = None
    original_content: Optional[str] = None
    metadata_json: Optional[str] = None
    generation_time_ms: Optional[int] = None
    expires_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None


class RecommendationResponse(RecommendationBase):
    """Schema for recommendation response with all fields"""
    recommendation_id: str
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    override_reason: Optional[str] = None
    original_content: Optional[str] = None
    metadata_json: Optional[str] = None
    generated_at: datetime
    generation_time_ms: Optional[int] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecommendationApprove(BaseModel):
    """Schema for approving a recommendation"""
    operator_id: str
    notes: Optional[str] = None


class RecommendationOverride(BaseModel):
    """Schema for overriding a recommendation"""
    operator_id: str
    new_title: Optional[str] = None
    new_content: Optional[str] = None
    reason: str


class RecommendationReject(BaseModel):
    """Schema for rejecting a recommendation"""
    operator_id: str
    reason: str


class BulkApproveRequest(BaseModel):
    """Schema for bulk approving recommendations"""
    operator_id: str
    recommendation_ids: List[str]


class BulkApproveResponse(BaseModel):
    """Schema for bulk approve response"""
    approved: int
    failed: int
    errors: List[str]


# ============================================================================
# Consent Schemas
# ============================================================================

class ConsentRequest(BaseModel):
    """Schema for consent update request"""
    user_id: str
    action: Literal["grant", "revoke"]


class ConsentHistoryItem(BaseModel):
    """Schema for consent history item"""
    action: str
    timestamp: Optional[str] = None


class ConsentResponse(BaseModel):
    """Schema for consent response"""
    user_id: str
    consent_status: bool
    consent_granted_at: Optional[str] = None
    consent_revoked_at: Optional[str] = None
    history: List[ConsentHistoryItem] = Field(default_factory=list)
