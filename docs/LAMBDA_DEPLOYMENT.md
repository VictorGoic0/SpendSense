# Lambda Deployment Guide

## SQLite Limitations in Lambda

### Current Implementation

SpendSense uses SQLite stored in `/tmp/spendsense.db` for the MVP deployment. This approach has the following characteristics:

**Advantages:**
- ✅ Simple setup, no external dependencies
- ✅ Fast read/write performance
- ✅ No additional AWS service costs
- ✅ Works immediately after deployment

**Limitations:**
- ⚠️ **Database resets on cold start**: SQLite files in `/tmp` are ephemeral and reset when Lambda containers are recycled
- ⚠️ **No persistence across invocations**: Data is lost when Lambda container is terminated
- ⚠️ **Concurrency limitations**: SQLite handles concurrent writes poorly (though WAL mode helps)
- ⚠️ **Size constraints**: `/tmp` has a 512MB limit (unlikely to be an issue for MVP)

### Auto-Seeding Solution

To mitigate the cold start data loss, SpendSense automatically seeds the database on startup:

1. **Detection**: On Lambda startup, the system checks if the database is empty
2. **Seeding**: If empty, synthetic data is automatically loaded from JSON files in the `data/` directory
3. **Idempotency**: If data already exists, seeding is skipped

This ensures:
- ✅ Data is available immediately after deployment
- ✅ Data is restored after cold starts
- ✅ No manual intervention required
- ✅ The `/ingest/` endpoint remains available for additional data

### Migration Path to RDS

For production workloads requiring persistent storage, migrate to Amazon RDS (PostgreSQL):

#### Step 1: Create RDS Instance

```bash
aws rds create-db-instance \
  --db-instance-identifier spendsense-db \
  --db-instance-class db.t3.micro \
  --engine postgresql \
  --master-username admin \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20 \
  --region us-east-2
```

#### Step 2: Update SAM Template

Update `template.yaml` to:
1. Add RDS connection string as parameter
2. Update `DATABASE_URL` environment variable
3. Add VPC configuration to Lambda (if RDS is in VPC)

#### Step 3: Update Connection String

Change `DATABASE_URL` from:
```
sqlite:///tmp/spendsense.db
```

To:
```
postgresql://admin:YOUR_PASSWORD@spendsense-db.xxxxx.us-east-2.rds.amazonaws.com:5432/spendsense
```

#### Step 4: Code Compatibility

No code changes required! SQLAlchemy models are database-agnostic:
- ✅ All models use standard SQLAlchemy types
- ✅ Relationships work identically
- ✅ Migrations can use Alembic (recommended for production)

#### Step 5: Deploy

```bash
sam build
sam deploy --parameter-overrides DatabaseUrl=postgresql://...
```

### Alternative: DynamoDB

For serverless-first architecture, consider DynamoDB:

**Advantages:**
- ✅ Fully managed, no server maintenance
- ✅ Automatic scaling
- ✅ Pay-per-use pricing
- ✅ Built-in backup and point-in-time recovery

**Considerations:**
- ⚠️ Requires code changes (DynamoDB SDK instead of SQLAlchemy)
- ⚠️ NoSQL data model (different query patterns)
- ⚠️ Cost can be higher for high-traffic applications

### Recommendations

**For MVP/Development:**
- ✅ Use SQLite in `/tmp` with auto-seeding (current implementation)
- ✅ Accept data loss on cold starts
- ✅ Use for demos and testing

**For Production:**
- ✅ Migrate to RDS PostgreSQL for persistent storage
- ✅ Set up automated backups
- ✅ Configure VPC security groups properly
- ✅ Use connection pooling (SQLAlchemy's `pool_pre_ping=True`)

**For High-Scale Production:**
- ✅ Consider RDS with read replicas
- ✅ Or migrate to DynamoDB for serverless architecture
- ✅ Implement caching layer (ElastiCache) for frequently accessed data

