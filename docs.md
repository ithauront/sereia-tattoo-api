# Ensure Datetime timezone aware

- Every datetime of the application must be timezone aware
- Every datetime must be in UTC
- Never use datetime.now() instead use datetime.now(timezone.utc)
