import sys
from typing import Optional
import typer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from models.user_model import User, UserRole
from database.database_setup import Base
from security_utilities.pass_hash import hash_password

DATABASE_URL= "sqlite:///./users.db"
app = typer.Typer(help="Seed users into the database (admin + regular).")


def get_session():
    """Create a standalone SQLAlchemy session for scripts (not FastAPI)."""
    engine = create_engine(DATABASE_URL, future=True)
    # Ensure tables exist (requires models imported above)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return SessionLocal()


def ensure_unique(session, email: str, user_name: str):
    email_exists = session.query(User).filter(User.email == email).first()
    if email_exists:
        typer.secho(f"✖ Email already exists: {email}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    uname_exists = session.query(User).filter(User.user_name == user_name).first()
    if uname_exists:
        typer.secho(f"✖ Username already exists: {user_name}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command("add-user")
def add_user(
    full_name: str = typer.Option(..., "--full-name", "-n", help="Full name"),
    user_name: str = typer.Option(..., "--username", "-u", help="Unique username"),
    email: str = typer.Option(..., "--email", "-e", help="Unique email"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True, confirmation_prompt=True),
    role: UserRole = typer.Option(UserRole.USER, "--role", "-r", case_sensitive=False, help="Role: USER / ADMIN / ANONYMOUS_USER"),
    active: bool = typer.Option(True, "--active/--inactive", help="Set user active flag"),
):
    """
    Add a single user with hashed password.
    """
    session = get_session()
    try:
        ensure_unique(session, email=email, user_name=user_name)

        hashed = hash_password(password)

        new_user = User(
            full_name=full_name,
            user_name=user_name,
            email=email,
            password=hashed,
            role=role,
            is_active=active
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        typer.secho(f"✔ User created: id={new_user.id}, email={new_user.email}, role={new_user.role.name}", fg=typer.colors.GREEN)

    except IntegrityError as ie:
        session.rollback()
        typer.secho(f"✖ Integrity error: {ie}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    finally:
        session.close()


@app.command("seed-admin")
def seed_admin(
    full_name: str = typer.Option("Admin", "--full-name", "-n"),
    user_name: str = typer.Option("admin", "--username", "-u"),
    email: str = typer.Option("admin@example.com", "--email", "-e"),
    password: Optional[str] = typer.Option(None, "--password", "-p", hide_input=True, confirmation_prompt=True),
    overwrite: bool = typer.Option(False, "--overwrite", help="If admin exists, update password & flags"),
):
    """
    Create an initial ADMIN user. If exists, optionally overwrite password/flags.
    """
    session = get_session()
    try:
        existing = session.query(User).filter(User.email == email).first()

        if existing and not overwrite:
            typer.secho(f"ℹ Admin already exists: {email} (use --overwrite to update)", fg=typer.colors.YELLOW)
            raise typer.Exit(code=0)

        if not password:
            # If not provided, prompt safely
            password = typer.prompt("Enter admin password", hide_input=True, confirmation_prompt=True)

        hashed = hash_password(password)

        if existing and overwrite:
            existing.full_name = full_name
            existing.user_name = user_name
            existing.password = hashed
            existing.role = UserRole.ADMIN
            existing.is_active = True
            session.commit()
            typer.secho(f"✔ Admin updated: {email}", fg=typer.colors.GREEN)
        else:
            ensure_unique(session, email=email, user_name=user_name)

            admin_user = User(
                full_name=full_name,
                user_name=user_name,
                email=email,
                password=hashed,
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            typer.secho(f"✔ Admin created: id={admin_user.id}, email={admin_user.email}", fg=typer.colors.GREEN)

    except IntegrityError as ie:
        session.rollback()
        typer.secho(f"✖ Integrity error: {ie}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    finally:
        session.close()


@app.command("bulk-csv")
def bulk_csv(
    path: str = typer.Argument(..., help="CSV with columns: full_name,user_name,email,password,role,is_active"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--no-skip-existing", help="Skip rows where email/username exists"),
):
    """
    Bulk import users from a CSV file.
    """
    import csv

    session = get_session()
    created = 0
    skipped = 0
    updated = 0

    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fn = row["full_name"].strip()
                un = row["user_name"].strip()
                em = row["email"].strip()
                pw = row["password"]
                role_raw = row.get("role", "USER").strip().upper()
                is_active_raw = row.get("is_active", "true").strip().lower()

                # Convert role
                try:
                    role = UserRole[role_raw]  # allows USER / ADMIN / ANONYMOUS_USER
                except KeyError:
                    typer.secho(f"✖ Invalid role '{role_raw}' for {em}. Skipping.", fg=typer.colors.RED)
                    skipped += 1
                    continue

                is_active = is_active_raw in ("true", "1", "yes", "y")

                existing_email = session.query(User).filter(User.email == em).first()
                existing_uname = session.query(User).filter(User.user_name == un).first()

                if (existing_email or existing_uname) and skip_existing:
                    skipped += 1
                    continue

                if existing_email and not skip_existing:
                    # update existing by email
                    existing_email.full_name = fn
                    existing_email.user_name = un
                    existing_email.password = hash_password(pw)
                    existing_email.role = role
                    existing_email.is_active = is_active
                    updated += 1
                else:
                    # new user
                    u = User(
                        full_name=fn,
                        user_name=un,
                        email=em,
                        password=hash_password(pw),
                        role=role,
                        is_active=is_active,
                    )
                    session.add(u)
                    created += 1

        session.commit()
        typer.secho(f"✔ Bulk import done. Created={created}, Updated={updated}, Skipped={skipped}", fg=typer.colors.GREEN)

    except FileNotFoundError:
        typer.secho(f"✖ CSV not found: {path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    finally:
        session.close()


if __name__ == "__main__":
    # `python scripts/seed_users.py --help` to see commands
    app()
