"""Regression test for the Drive `User` after_insert hook signature introspection.

`drive/drive/utils/users.py::assign_drive_role_and_create_settings` annotated its
`user` parameter as `User` without importing it. Frappe introspects every doc-event
handler's signature via `inspect.signature()` (`_accepts_method_argument`,
frappe/model/document.py), so on EVERY `User.insert` the unresolved annotation was
evaluated and raised `NameError: name 'User' is not defined` — breaking all user
creation (and any app install that seeds a User) on sites with drive installed.

The fix makes annotations non-evaluating (`from __future__ import annotations`) plus
a `TYPE_CHECKING` import, so `inspect.signature()` sees a lazy string and never
evaluates `User`.

This test reproduces the exact broken introspection — `inspect.signature()` on the
handler — which deterministically raised before the fix and succeeds after. It
creates no documents (so it leaves no data and does not depend on ERPNext test
records). The hook's runtime side effects (Drive User role + Drive Settings on a new
User) are verified separately via the dev console — see issue PR-Foundry/framework#40.
"""

import inspect
import unittest

from drive.utils.users import assign_drive_role_and_create_settings


class TestDriveUserHookSignature(unittest.TestCase):
    def test_signature_introspection_does_not_raise_nameerror(self):
        # Before the fix this raised `NameError: name 'User' is not defined` — the
        # exact failure Frappe hit in _accepts_method_argument on every User.insert.
        # Letting it raise here IS the pre-fix regression signal.
        sig = inspect.signature(assign_drive_role_and_create_settings)

        # The `user` annotation must be a lazy string (PEP 563), not an evaluated name.
        self.assertEqual(sig.parameters["user"].annotation, "User")
        self.assertIn("method", sig.parameters)
