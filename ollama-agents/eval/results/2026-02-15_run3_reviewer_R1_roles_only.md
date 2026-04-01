Thinking...
Okay, let's start by looking at the provided context and the task. The user wants an audit of the PLAN and TESTS sections, focusing on inconsistencies categorized as P0, P1, or P2 with evidence and a remediation plan. Since the task mentions roles only and no ownership, I need to focus on the structure and content of the test plan and test cases, ensuring they align with the requirements and best practices.

First, I'll check the sections mentioned in the context. The PLAN includes sections like "Cobertura por endpoint," "Fixtures/Factories," "Estrategia de DB en tests," "Casos límite y regresión," and "Checklist de Definition of Done para tests." The TESTS section has a detailed table with test cases and their expected outcomes. 

Looking at the test cases, for example, T018 mentions checking password hashing during user registration. That's a good unit test. However, I should check if all endpoints have corresponding test cases. The "Cobertura por endpoint" section lists each endpoint with expected codes and error formats, but I need to cross-reference this with the actual test cases in the table.

Another point is the error format. The context mentions that errors should follow a specific structure with code, message, details, and trace_id. Looking at the test cases, some entries mention the format, like T005 expecting a specific error code. However, I should verify if all test cases that expect errors have the correct format specified.

In the "Fixtures/Factories" section, there's a mention of `user_factory`, `property_factory`, `auth_token_factory`, and `test_client`. These seem appropriate, but I need to ensure that these fixtures are used in the test cases. For example, T007 tests access without authentication, which would require the `test_client` fixture to simulate a request without a token.

The "Estrategia de DB en tests" uses SQLite in memory, which is good for isolation. However, the gap section mentions that real database persistence isn't tested. This might be a P2 issue if the application relies on specific database behaviors not covered by SQLite.

Looking at the test cases, T013 mentions creating an invalid property with a negative price, expecting a 422. That's covered, but are all validation scenarios covered? For example, the "Casos límite y regresión" section mentions testing min and max values for price, but I need to check if the test cases include these.

In the "Checklist de Definition of Done para tests," there's a mention of verifying the error format. However, the test cases don't explicitly state that they check the structure of the error response beyond the code and message. This could be a P1 issue if the actual implementation requires more detailed error checks.

Also, in the "Riesgos de testing y mitigaciones," the user mentions testing roles in protected endpoints. Looking at the test cases, T008 tests access with a visitor role, which is covered. However, are all roles (admin, agent, visitor) tested in all relevant endpoints? For example, T012 tests creating a property with admin/agent, but what about other endpoints that might have different role requirements?

Another point is the use of trace_id in error responses. The context's error format includes trace_id, but the test cases don't mention checking this field. This might be a P2 issue if the trace_id is required for debugging and monitoring.

In the "Gaps" section, it's noted that e2e tests aren't done for the frontend. However, the task is about roles only, so maybe this isn't a priority here. Still, if the test plan claims to cover all aspects but misses e2e, that's a gap.

Overall, I need to go through each section and cross-check with the test cases and requirements, looking for any discrepancies in coverage, error handling, fixture usage, and role-based access tests.
...done thinking.

### **AUDIT PLAN + TESTS (ROLES ONLY)**  
**P0/P1/P2 Inconsistencies with Evidence & Remediation Plan**  

---

### **1. Inconsistency: Incomplete Error Format Validation (P1)**  
**Evidence**:  
- **Context** specifies error responses must include:  
  ```json  
  { "error": { "code": "...", "message": "...", "details": {} }, "trace_id": "..." }  
  ```  
- **Test Cases** (e.g., T005, T017) only verify `code` and `message` but **omit validation of `trace_id`** and `details` fields.  
- **Cobertura por endpoint** sections for `/auth/login`, `/properties`, etc., **do not explicitly require testing** the full error structure.  

**Remediation**:  
- **Add test cases** to validate `trace_id` and `details` in all error responses (e.g., T005 → T005a: "Validate `trace_id` in `invalid_token` error").  
- Update **Cobertura por endpoint** tables to explicitly require **error structure validation** (e.g., "Validate full error format: code, message, details, trace_id").  

---

### **2. Inconsistency: Missing Role-Based Access Tests for Non-Admin/Agent Endpoints (P2)**  
**Evidence**:  
- **Test Cases** (e.g., T008) only test **`/properties`** with a **visitor role**.  
- **No test cases** exist for **other protected endpoints** (e.g., `/auth/refresh`, `/auth/register`) with **roles other than admin/agent** (e.g., visitor).  
- **Cobertura por endpoint** sections for `/auth/register`, `/auth/login`, etc., **do not specify role-based access checks**.  

**Remediation**:  
- Add test cases for **all protected endpoints** with **non-admin/agent roles** (e.g., T020: "Test `/auth/register` with visitor role → 403 Forbidden").  
- Update **Cobertura por endpoint** tables to include **role-based access checks** for **all endpoints**.  

---

### **3. Inconsistency: Lack of Edge Case Coverage for Pagination/Filters (P1)**  
**Evidence**:  
- **Test Cases** (T009–T011) cover basic pagination/filters but **omit edge cases**:  
  - `page=0`, `per_page=0`, `price_min > price_max`, `sort=invalid_field`, `dir=invalid_direction` (e.g., `dir=ascend`).  
- **Cobertura por endpoint** sections for `/properties` **do not explicitly require testing** these edge cases.  

**Remediation**:  
- Add test cases for **invalid pagination/filter parameters** (e.g., T019: "Test `/properties?sort=invalid_field` → 422 Unprocessable Entity").  
- Update **Cobertura por endpoint** tables to include **edge case coverage** for **all parameters**.  

---

### **4. Inconsistency: Missing Tests for Password Hashing in DB (P1)**  
**Evidence**:  
- **Test Case T018** checks password hashing during registration but **does not verify** that the **stored hash** matches the expected algorithm (e.g., bcrypt).  
- **Cobertura por endpoint** sections for `/auth/register` **do not specify** testing hash algorithm compliance.  

**Remediation**:  
- Add test case to **validate hash algorithm** (e.g., T018a: "Verify stored password is bcrypt hash").  
- Update **Cobertura por endpoint** for `/auth/register` to include **hash algorithm verification**.  

---

### **5. Inconsistency: Incomplete Coverage of Error Codes in `/properties` (P2)**  
**Evidence**:  
- **Cobertura por endpoint** for `/properties` lists **expected codes (200, 422)** but **omits codes** like **404 (T017)** and **401 (T007)**.  
- **Test Cases** (T017) explicitly test 404 but **do not cover** other codes (e.g., 401 for unauthenticated requests).  

**Remediation**:  
- Update **Cobertura por endpoint** for `/properties` to include **all expected codes** (200, 401, 404, 422).  
- Add test cases for **unauthenticated requests** to `/properties` (e.g., T021: "Test `/properties` without auth → 401 Unauthorized").  

---

### **6. Inconsistency: Lack of Tests for Token Expiry in `/auth/refresh` (P1)**  
**Evidence**:  
- **Test Cases** (T006) test invalid tokens but **do not cover** **expired tokens**.  
- **Cobertura por endpoint** for `/auth/refresh` **does not specify** testing token expiry.  

**Remediation**:  
- Add test case for **expired refresh token** (e.g., T006a: "Test `/auth/refresh` with expired token → 403 Forbidden").  
- Update **Cobertura por endpoint** for `/auth/refresh` to include **token expiry validation**.  

---

### **7. Inconsistency: Missing Tests for Role-Based Access in `/auth/refresh` (P2)**  
**Evidence**:  
- **Test Cases** (T006) only test invalid tokens but **do not check** if **unauthorized roles** (e.g., visitor) can access `/auth/refresh`.  
- **Cobertura por端点** for `/auth/refresh` **does not mention role-based access checks**.  

**Remediation**:  
- Add test case for **unauthorized role** accessing `/auth/refresh` (e.g., T022: "Test `/auth/refresh` with visitor role → 403 Forbidden").  
- Update **Cobertura por endpoint** for `/auth/refresh` to include **role-based access checks**.  

---

### **8. Inconsistency: No Tests for Rate Limiting or Throttling (P2)**  
**Evidence**:  
- **No test cases** exist for **rate limiting** (e.g., excessive login attempts).  
- **Cobertura por endpoint** sections **do not mention** testing rate limiting.  

**Remediation**:  
- Add test cases for **rate limiting** (e.g., T023: "Test 5 failed `/auth/login` attempts → 429 Too Many Requests").  
- Update **Cobertura por endpoint** for `/auth/login` to include **rate limiting checks**.  

---

### **9. Inconsistency: Incomplete Fixtures/Factories Usage in Test Cases (P1)**  
**Evidence**:  
- **Test Cases** (e.g., T007) **do not explicitly reference** fixtures like `test_client` or `auth_token_factory` in their descriptions.  
- **Fixtures/Factories** section **does not map** fixtures to specific test cases (e.g., "T007 uses `test_client` to simulate unauthenticated requests").  

**Remediation**:  
- Update **Test Cases** to **explicitly reference fixtures** used (e.g., T007: "Uses `test_client` to simulate unauthenticated request").  
- Add a **mapping table** in **Fixtures/Factories** to link fixtures to test cases.  

---

### **10. Inconsistency: No Tests for Data Validation on `/auth/register` (P2)**  
**Evidence**:  
- **Test Cases** (T018) only test password hashing but **do not check** validation of other fields (e.g., missing email, invalid username).  
- **Cobertura por endpoint** for `/auth/register` **does not specify** testing data validation.  

**Remediation**:  
- Add test cases for **invalid registration data** (e.g., T024: "Test `/auth/register` with missing email → 422 Unprocessable Entity").  
- Update **Cobertura por endpoint** for `/auth/register` to include **data validation checks**.  

---

### **Summary of Remediation Actions**  
| **Inconsistency** | **Remediation** |  
|-------------------|-----------------|  
| Incomplete error format validation | Add test cases for `trace_id` and `details` fields. |  
| Missing role-based access tests | Add tests for all endpoints with non-admin/agent roles. |  
| Edge case coverage for pagination/filters | Add tests for invalid parameters (e.g., `page=0`, `sort=invalid`). |  
| Password hashing verification | Add test to validate hash algorithm (e.g., bcrypt). |  
| Incomplete error code coverage | Update Cobertura tables and add tests for 401, 404. |  
| Token expiry in `/auth/refresh` | Add test for expired token. |  
| Role-based access in `/auth/refresh` | Add test for unauthorized role. |  
| Rate limiting tests | Add test for excessive login attempts. |  
| Fixtures/Factories mapping | Reference fixtures in test cases and add mapping table. |  
| Data validation on `/auth/register` | Add tests for invalid registration data. |  

**Impact**: Without these fixes, the test plan risks **incomplete coverage**, **uncaught edge cases**, and **non-compliance with error/response standards**, leading to **production bugs** and **security vulnerabilities**.

