# Product Context: SpendSense

## Why This Project Exists
SpendSense addresses the gap between raw financial transaction data and actionable financial education. Most people have access to their transaction history but lack the tools to:
- Understand their financial behavioral patterns
- Receive personalized, relevant financial education
- Make informed decisions based on their specific financial situation

## Problems It Solves

### For Users
1. **Pattern Recognition**: Automatically detects recurring subscriptions, savings habits, credit utilization, and income patterns
2. **Personalized Education**: Delivers content tailored to their specific financial persona (not generic advice)
3. **Transparency**: Every recommendation includes a plain-language rationale citing specific user data
4. **Consent Control**: Users can opt-in/opt-out of recommendations at any time

### For Operators
1. **Oversight**: Review and approve all AI-generated recommendations before users see them
2. **Quality Control**: Override or reject recommendations that don't meet standards
3. **Metrics**: Track coverage, explainability, latency, and auditability
4. **User Insights**: View detailed financial signals and persona assignments for each user

## How It Should Work

### User Journey
1. User data is ingested (synthetic Plaid-style JSON)
2. System computes behavioral features (30-day and 180-day windows)
3. User is assigned to one of 5 personas based on detected patterns
4. If user has consented, AI generates personalized recommendations
5. Recommendations go through guardrails (consent check, tone validation, eligibility)
6. Recommendations enter approval queue for operator review
7. Once approved, recommendations appear in user dashboard
8. User can view educational content with transparent rationales

### Operator Journey
1. View dashboard with metrics (total users, persona distribution, pending approvals)
2. Browse user list with persona and consent status
3. Click into user to see detailed signals and recommendations
4. Review pending recommendations in approval queue
5. Approve, reject, or override recommendations
6. Run evaluation to generate metrics and Parquet exports

## User Experience Goals

### Operator Interface
- Clear metrics dashboard showing system health
- Easy navigation between users and recommendations
- Efficient bulk approval workflow
- Detailed user signal visualization
- Override workflow with reason logging

### User Interface
- Simple consent toggle with clear explanation
- Clean recommendation feed with educational content
- Transparent rationales showing why each recommendation was made
- No shaming language or judgmental tone
- Empowering, educational messaging

## Key Design Principles
1. **Explainability First**: Every recommendation must cite specific user data
2. **Consent is Mandatory**: No recommendations without explicit opt-in
3. **No Financial Advice**: Educational content only, with mandatory disclaimers
4. **Supportive Tone**: Empowering language, no shaming or judgment
5. **Operator Control**: All AI outputs require human approval before user visibility

