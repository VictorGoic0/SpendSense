# Environment Variables Example

Copy this file to `.env` and fill in your actual values.

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# Database Configuration
DATABASE_URL=sqlite:///./spendsense.db

# AWS Configuration (for S3 exports)
# Note: If using AWS CLI credentials (aws configure), these are optional
# The script will use AWS CLI credentials if these are not set
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_DEFAULT_REGION=us-east-2
S3_BUCKET_NAME=spendsense-analytics-goico
```

