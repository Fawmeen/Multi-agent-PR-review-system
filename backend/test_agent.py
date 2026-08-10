import asyncio
import json
from app.orchestrator.graph import build_review_graph

SAMPLE_DIFF = """
diff --git a/src/auth/login.py b/src/auth/login.py
new file mode 100644
index 0000000..a1b2c3d
--- /dev/null
+++ b/src/auth/login.py
@@ -0,0 +1,15 @@
+import sqlite3
+
+def login(username, password):
+    conn = sqlite3.connect("users.db")
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    result = conn.execute(query)
+    user = result.fetchone()
+    if user:
+        return True
+    return False
+
+def generate_token(user_id):
+    secret = "super-secret-key-hardcoded"
+    return jwt.encode({"user_id": user_id}, secret, algorithm="HS256")
+"""

async def main():
    graph = build_review_graph()
    initial_state = {
        "diff": SAMPLE_DIFF,
        "repository": "test/repo",
        "pr_number": 1,
        "workflow_run_id": "run-openrouter-1",
        "findings": [],
        "consolidated_findings": [],
        "agent_errors": {},
    }
    print("Running the graph with OpenRouter...")
    final_state = await graph.ainvoke(initial_state)
    print("\n✅ Graph completed.")
    print(f"Number of raw findings: {len(final_state.get('findings', []))}")
    consolidated = final_state.get('consolidated_findings', [])
    print(f"Consolidated findings: {json.dumps(consolidated, indent=2)}")
    print(f"Agent errors: {final_state.get('agent_errors')}")

if __name__ == "__main__":
    asyncio.run(main())