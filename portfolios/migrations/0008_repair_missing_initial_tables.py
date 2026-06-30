from django.db import migrations


def create_missing_initial_tables(apps, schema_editor):
    if schema_editor.connection.vendor != 'sqlite':
        return

    cursor = schema_editor.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}

    if 'portfolios_theme' not in existing_tables:
        cursor.execute(
            "CREATE TABLE portfolios_theme ("
            "id integer PRIMARY KEY AUTOINCREMENT, "
            "slug varchar(100) NOT NULL UNIQUE, "
            "name varchar(100) NOT NULL, "
            "description text NOT NULL, "
            "template_path varchar(255) NOT NULL, "
            "preview_image varchar(255) NOT NULL, "
            "palette text NOT NULL DEFAULT '{}', "
            "is_active bool NOT NULL DEFAULT 1, "
            "created_at datetime NOT NULL"
            ")"
        )

    if 'portfolios_education' not in existing_tables:
        cursor.execute(
            "CREATE TABLE portfolios_education ("
            "id integer PRIMARY KEY AUTOINCREMENT, "
            "degree varchar(100) NOT NULL, "
            "field_of_study varchar(255) NOT NULL, "
            "institution varchar(255) NOT NULL, "
            "start_year integer NOT NULL, "
            "end_year integer NULL, "
            "description text NOT NULL, "
            "honor varchar(100) NOT NULL, "
            "order_index integer NOT NULL DEFAULT 0, "
            "created_at datetime NOT NULL, "
            "updated_at datetime NOT NULL, "
            "profile_id bigint NOT NULL REFERENCES portfolios_profile(id) DEFERRABLE INITIALLY DEFERRED"
            ")"
        )

    if 'portfolios_contactlink' not in existing_tables:
        cursor.execute(
            "CREATE TABLE portfolios_contactlink ("
            "id integer PRIMARY KEY AUTOINCREMENT, "
            "label varchar(100) NOT NULL, "
            "value varchar(255) NOT NULL, "
            "url varchar(200) NOT NULL DEFAULT '', "
            "link_type varchar(20) NOT NULL DEFAULT 'link', "
            "order_index integer NOT NULL DEFAULT 0, "
            "profile_id bigint NOT NULL REFERENCES portfolios_profile(id) DEFERRABLE INITIALLY DEFERRED"
            ")"
        )

    if 'portfolios_researchinterest' not in existing_tables:
        cursor.execute(
            "CREATE TABLE portfolios_researchinterest ("
            "id integer PRIMARY KEY AUTOINCREMENT, "
            "title varchar(255) NOT NULL, "
            "description text NOT NULL, "
            "tags varchar(255) NOT NULL, "
            "order_index integer NOT NULL DEFAULT 0, "
            "profile_id bigint NOT NULL REFERENCES portfolios_profile(id) DEFERRABLE INITIALLY DEFERRED"
            ")"
        )

    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS portfolios_theme_slug_uniq ON portfolios_theme(slug)"
    )


class Migration(migrations.Migration):

    dependencies = [
        ('portfolios', '0007_repair_profile_profile_columns'),
    ]

    operations = [
        migrations.RunPython(create_missing_initial_tables, migrations.RunPython.noop),
    ]
