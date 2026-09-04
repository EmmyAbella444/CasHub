from My_library import check_password, database_worker


def test_register_hashes_password_and_login_works(app, client, auth):
    response = auth.register()
    assert b"Account created" in response.data

    db = database_worker(app.config["DATABASE"])
    user = db.get(
        "SELECT email, password FROM users WHERE email = ?",
        ("emmy@example.com",),
    )
    db.close()

    assert user is not None
    assert user[1] != "Strong123!"
    assert check_password("Strong123!", user[1])

    response = auth.login()
    assert b"Recent Posts from your peers" in response.data


def test_registration_rejects_duplicate_email(client, auth):
    auth.register()
    response = auth.register(name="Another Emmy")
    assert b"already exists" in response.data


def test_login_rejects_bad_password(client, auth):
    auth.register()
    response = auth.login(password="Wrong123!")
    assert b"Incorrect email or password" in response.data


def test_protected_page_redirects_to_login(client):
    response = client.get("/home", follow_redirects=True)
    assert b"Please log in to continue" in response.data
    assert b"Login" in response.data
