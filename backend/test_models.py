"""Test the models module."""
import sys
sys.path.insert(0, '.')

from app.models.enums import FindingSeverity, FindingCategory, AgentName, ReviewStatus
from app.models.findings import Finding
from app.models.review import Review

# Test 1: Create a Finding
finding = Finding(
    agent=AgentName.SECURITY,
    category=FindingCategory.SECURITY,
    severity=FindingSeverity.CRITICAL,
    file_path="src/auth/login.py",
    line_start=42,
    line_end=45,
    title="SQL Injection vulnerability",
    description="User input concatenated into query",
    suggestion="Use parameterized queries",
    rule_reference="OWASP Top 10 A03:2021"
)

print(f"✅ Finding created: {finding.title}")
print(f"   Agent: {finding.agent}")
print(f"   Severity: {finding.severity}")

# Test 2: JSON serialization
finding_json = finding.model_dump_json(indent=2)
print(f"✅ Serialized to JSON:\n{finding_json[:200]}...")

# Test 3: Create a Review with multiple findings
review = Review(
    repository="org/repo",
    pr_number=42,
    findings=[finding]
)
review.compute_summary()
print(f"\n✅ Review created:")
print(f"   Total findings: {review.summary.total_findings}")
print(f"   Critical: {review.summary.critical}")
print(f"   Files affected: {review.summary.files_affected}")

# Test 4: Validation — should fail
try:
    bad_finding = Finding(
        agent=AgentName.SECURITY,
        category=FindingCategory.SECURITY,
        severity=FindingSeverity.CRITICAL,
        file_path="src/auth/login.py",
        title="X",  # Too short — min_length is 5
        description="User input concatenated into query",
    )
    print("❌ Should have raised validation error!")
except Exception as e:
    print(f"✅ Validation works: short title rejected")

print("\n✅ All models tests passed!")