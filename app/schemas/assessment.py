from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Industry(str, Enum):
    it_services = "it_services"
    fintech = "fintech"
    healthcare = "healthcare"
    ecommerce = "ecommerce"
    manufacturing = "manufacturing"
    education = "education"
    real_estate = "real_estate"
    legal = "legal"
    accounting = "accounting"
    other = "other"


class CompanySize(str, Enum):
    startup = "startup"       # <50 employees
    sme = "sme"               # 50-500
    large = "large"           # 500-5000
    enterprise = "enterprise" # 5000+


class DocumentCategory(str, Enum):
    privacy_policy = "privacy_policy"
    consent_form = "consent_form"
    data_flow_diagram = "data_flow_diagram"
    dpia = "dpia"
    processing_records = "processing_records"
    breach_procedure = "breach_procedure"
    retention_policy = "retention_policy"
    vendor_agreement = "vendor_agreement"
    other = "other"


class AssessmentCreate(BaseModel):
    company_name: str
    industry: Industry
    company_size: CompanySize
    description: str | None = None


class AssessmentResponse(BaseModel):
    id: str
    company_name: str
    industry: str
    company_size: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    assessment_id: str
    filename: str
    file_type: str
    document_category: str
    text_length: int
    uploaded_at: datetime
