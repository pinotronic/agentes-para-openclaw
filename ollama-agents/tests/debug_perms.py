#!/usr/bin/env python3
"""Quick debug test for permissions module."""
import sys
sys.path.insert(0, '/home/administrador/.openclaw/workspace/ollama-agents')

from agents.permissions import (
    PermissionMode, PermissionPolicy, implementer_policy,
    code_critic_policy, get_agent_policy
)

def test(name, expr):
    result = bool(expr)
    status = "PASS" if result else "FAIL"
    print(f"[{status}] {name}: {result}")
    return result

def run():
    all_pass = True
    
    # Test PermissionMode.level
    all_pass &= test("READ_ONLY.level == 0", PermissionMode.READ_ONLY.level == 0)
    all_pass &= test("WORKSPACE_WRITE.level == 1", PermissionMode.WORKSPACE_WRITE.level == 1)
    all_pass &= test("DANGER_FULL_ACCESS.level == 2", PermissionMode.DANGER_FULL_ACCESS.level == 2)
    
    # Test satisfies
    all_pass &= test("READ_ONLY.satisfies(READ_ONLY)", PermissionMode.READ_ONLY.satisfies(PermissionMode.READ_ONLY))
    all_pass &= test("DANGER_FULL_ACCESS.satisfies(READ_ONLY)", PermissionMode.DANGER_FULL_ACCESS.satisfies(PermissionMode.READ_ONLY))
    all_pass &= test("not READ_ONLY.satisfies(DANGER_FULL_ACCESS)", not PermissionMode.READ_ONLY.satisfies(PermissionMode.DANGER_FULL_ACCESS))
    
    # Test PermissionPolicy default
    policy = PermissionPolicy()
    all_pass &= test("default can_use bash DANGER", policy.can_use("bash", PermissionMode.DANGER_FULL_ACCESS))
    all_pass &= test("default can_use read_file READ", policy.can_use("read_file", PermissionMode.READ_ONLY))
    all_pass &= test("default can_use glob READ", policy.can_use("glob", PermissionMode.READ_ONLY))
    
    # Test PermissionPolicy with allowed_tools
    policy2 = PermissionPolicy(allowed_tools=frozenset({"read", "glob"}))
    all_pass &= test("restricted can_use read READ", policy2.can_use("read", PermissionMode.READ_ONLY))
    all_pass &= test("restricted can_use glob READ", policy2.can_use("glob", PermissionMode.READ_ONLY))
    all_pass &= test("restricted NOT can_use bash DANGER", not policy2.can_use("bash", PermissionMode.DANGER_FULL_ACCESS))
    
    # Test implementer_policy
    ip = implementer_policy()
    all_pass &= test("implementer can_use read READ", ip.can_use("read", PermissionMode.READ_ONLY))
    all_pass &= test("implementer can_use write WRITE", ip.can_use("write", PermissionMode.WORKSPACE_WRITE))
    all_pass &= test("implementer can_use edit WRITE", ip.can_use("edit", PermissionMode.WORKSPACE_WRITE))
    all_pass &= test("implementer can_use bash DANGER", ip.can_use("bash", PermissionMode.DANGER_FULL_ACCESS))
    all_pass &= test("implementer NOT can_use web_search READ", not ip.can_use("web_search", PermissionMode.READ_ONLY))
    
    print()
    if all_pass:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    return all_pass

if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
