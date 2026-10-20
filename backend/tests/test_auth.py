import json
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from pydantic import SecretStr

from app.core import supabase_auth
from app.database.invitation import PublicationInvitation


class AuthenticatedAccountTests(unittest.TestCase):
    def test_supabase_user_endpoint_verifies_and_normalizes_identity(self):
        user_id = uuid4()

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return json.dumps(
                    {
                        "id": str(user_id),
                        "email": "Owner@Example.com",
                        "email_confirmed_at": "2026-10-20T12:00:00Z",
                        "is_anonymous": False,
                    }
                ).encode()

        with (
            patch.object(
                supabase_auth.settings,
                "SUPABASE_PUBLISHABLE_KEY",
                SecretStr("test-publishable-key"),
            ),
            patch.object(supabase_auth, "urlopen", return_value=Response()) as open_url,
        ):
            user = supabase_auth.get_authenticated_user("test-access-token")

        self.assertEqual(user.id, user_id)
        self.assertEqual(user.email, "owner@example.com")
        request = open_url.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/auth/v1/user"))
        self.assertEqual(
            request.get_header("Authorization"), "Bearer test-access-token"
        )

    def test_unconfirmed_email_cannot_manage_publications(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return json.dumps(
                    {
                        "id": str(uuid4()),
                        "email": "owner@example.com",
                        "email_confirmed_at": None,
                    }
                ).encode()

        with (
            patch.object(
                supabase_auth.settings,
                "SUPABASE_PUBLISHABLE_KEY",
                SecretStr("test-publishable-key"),
            ),
            patch.object(supabase_auth, "urlopen", return_value=Response()),
        ):
            with self.assertRaises(HTTPException) as error:
                supabase_auth.get_authenticated_user("test-access-token")

        self.assertEqual(error.exception.status_code, 403)

    def test_missing_bearer_token_is_rejected(self):
        with self.assertRaises(HTTPException) as error:
            supabase_auth.require_authenticated_user(None)

        self.assertEqual(error.exception.status_code, 401)

    def test_account_must_be_on_the_server_invitation_allowlist(self):
        user_id = uuid4()
        user = supabase_auth.AuthenticatedUser(user_id, "owner@example.com")
        db = Mock()
        db.get.side_effect = [None, None]

        with patch.object(supabase_auth, "get_authenticated_user", return_value=user):
            with self.assertRaises(HTTPException) as error:
                supabase_auth.require_authenticated_user("Bearer token", db)

        self.assertEqual(error.exception.status_code, 403)

    def test_invited_email_is_bound_to_its_verified_user_id(self):
        user_id = uuid4()
        user = supabase_auth.AuthenticatedUser(user_id, "owner@example.com")
        invitation = PublicationInvitation(email=user.email)
        db = Mock()
        db.get.side_effect = [invitation, None]

        with patch.object(supabase_auth, "get_authenticated_user", return_value=user):
            authenticated = supabase_auth.require_authenticated_user("Bearer token", db)

        self.assertEqual(authenticated, user)
        db.add.assert_called_once()
        self.assertEqual(db.add.call_args.args[0].id, user_id)
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
