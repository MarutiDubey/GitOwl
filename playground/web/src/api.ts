export interface Finding {
  severity: string;
  title: string;
  message: string;
  file: string | null;
  line: number | null;
  suggestion: string | null;
}

export interface ReviewResponse {
  risk: string;
  summary: string;
  findings: Finding[];
  files_changed: number;
  added_lines: number;
  removed_lines: number;
}

export class ReviewApiError extends Error {}

export async function reviewDiff(diff: string): Promise<ReviewResponse> {
  const res = await fetch("/api/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ diff }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail ?? `request failed (${res.status})`;
    throw new ReviewApiError(detail);
  }
  return res.json();
}

export const EXAMPLE_DIFF = `diff --git a/auth.py b/auth.py
index 1111111..2222222 100644
--- a/auth.py
+++ b/auth.py
@@ -1,5 +1,6 @@
 import hashlib

 def check_password(pw: str, stored_hash: str) -> bool:
-    return hashlib.md5(pw.encode()).hexdigest() == stored_hash
+    computed = hashlib.md5(pw.encode()).hexdigest()
+    return computed == stored_hash
`;
