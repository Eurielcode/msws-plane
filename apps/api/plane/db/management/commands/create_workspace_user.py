# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import uuid

# Django imports
from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand, CommandError
from django.utils import timezone

# Third party imports
from zxcvbn import zxcvbn

# Module imports
from plane.db.models import Profile, User, Workspace, WorkspaceMember


class Command(BaseCommand):
    help = (
        "Create a user with a password and add them to a workspace directly, "
        "bypassing the email-based signup/invite flow entirely. Useful when "
        "outbound email isn't working."
    )

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, required=True, help="Email of the user to create")
        parser.add_argument("--password", type=str, required=True, help="Password to set for the user")
        parser.add_argument("--workspace_slug", type=str, required=True, help="Slug of the workspace to add them to")
        parser.add_argument(
            "--role",
            type=int,
            default=15,
            help="Workspace role: 20=Admin, 15=Member, 5=Guest (default: 15)",
        )
        parser.add_argument("--first_name", type=str, default="", help="First name (optional)")
        parser.add_argument("--last_name", type=str, default="", help="Last name (optional)")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"]
        workspace_slug = options["workspace_slug"]
        role = options["role"]
        first_name = options["first_name"]
        last_name = options["last_name"]

        if role not in (20, 15, 5):
            raise CommandError("--role must be 20 (Admin), 15 (Member), or 5 (Guest)")

        results = zxcvbn(password)
        if results["score"] < 3:
            raise CommandError("Password is too weak. Use a longer, less predictable password.")

        workspace = Workspace.objects.filter(slug=workspace_slug).first()
        if workspace is None:
            raise CommandError(f"No workspace found with slug '{workspace_slug}'")

        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create(
                email=email,
                username=uuid.uuid4().hex,
                first_name=first_name,
                last_name=last_name,
                password=make_password(password),
                is_password_autoset=False,
                is_active=True,
                last_active=timezone.now(),
            )
            Profile.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(f"Created user {email}"))
        else:
            user.set_password(password)
            user.is_password_autoset = False
            user.is_active = True
            user.save(update_fields=["password", "is_password_autoset", "is_active"])
            self.stdout.write(self.style.SUCCESS(f"User {email} already existed, password updated"))

        member, created = WorkspaceMember.objects.get_or_create(
            workspace=workspace,
            member=user,
            defaults={"role": role, "is_active": True},
        )
        if not created:
            member.role = role
            member.is_active = True
            member.save(update_fields=["role", "is_active"])

        self.stdout.write(
            self.style.SUCCESS(f"{email} is now a member (role={role}) of workspace '{workspace_slug}'.")
        )
        self.stdout.write(f"They can sign in directly with email {email} and the password you set.")
