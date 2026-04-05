#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/administrador/.openclaw/workspace/ollama-agents')

from agents.permissions import PermissionPolicy, PermissionMode, implementer_policy

p = PermissionPolicy()
print("default_mode:", p.default_mode)
print("allowed_tools:", p.allowed_tools)
print("can_use bash DANGER:", p.can_use("bash", PermissionMode.DANGER_FULL_ACCESS))
print("can_use read_file READ:", p.can_use("read_file", PermissionMode.READ_ONLY))
print("requires read_file:", p.requires("read_file"))

ip = implementer_policy()
print("\nimplementer default_mode:", ip.default_mode)
print("implementer allowed_tools sample:", list(ip.allowed_tools)[:5] if ip.allowed_tools else None)
print("implementer can_use read READ:", ip.can_use("read", PermissionMode.READ_ONLY))
print("implementer can_use write WRITE:", ip.can_use("write", PermissionMode.WORKSPACE_WRITE))
print("implementer can_use bash DANGER:", ip.can_use("bash", PermissionMode.DANGER_FULL_ACCESS))
