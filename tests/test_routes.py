from My_library import database_worker


def create_activity(client, title="Community garden", content="Organized a planting day and reflected on teamwork."):
    return client.post(
        "/home",
        data={
            "post-title": title,
            "post-content": content,
            "clubs[]": ["Peace Forum"],
            "date": "2026-09-01",
        },
        follow_redirects=True,
    )


def test_activity_comment_like_and_pdf(app, client, auth):
    auth.register()
    auth.login()

    response = create_activity(client)
    assert b"Community garden" in response.data
    assert b"Activity added" in response.data

    response = client.post(
        "/post/1/add_comment",
        data={"comment": "Wonderful initiative!"},
        follow_redirects=True,
    )
    assert b"Wonderful initiative!" in response.data

    response = client.post("/post/1/like", follow_redirects=True)
    assert response.status_code == 200

    db = database_worker(app.config["DATABASE"])
    like_count = db.get(
        "SELECT COUNT(*) FROM likes WHERE post_id = ?",
        (1,),
    )[0]
    db.close()
    assert like_count == 1

    response = client.get("/save_pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_sql_text_with_apostrophe_is_saved_safely(app, client, auth):
    auth.register()
    auth.login()

    response = create_activity(
        client,
        title="Today's reflection",
        content="I learned that a teammate's perspective can improve the plan.",
    )
    assert response.status_code == 200

    db = database_worker(app.config["DATABASE"])
    post = db.get("SELECT title, content FROM posts WHERE id = ?", (1,))
    db.close()

    assert post[0] == "Today's reflection"
    assert "teammate's" in post[1]


def test_user_cannot_delete_another_users_post(app, client, auth):
    auth.register()
    auth.login()
    create_activity(client)

    auth.logout()
    auth.register(name="Jordan", email="jordan@example.com")
    auth.login(email="jordan@example.com")

    response = client.post("/delete_post", data={"post_id": 1})
    assert response.status_code == 403

    db = database_worker(app.config["DATABASE"])
    post = db.get("SELECT id FROM posts WHERE id = ?", (1,))
    db.close()
    assert post is not None


def test_owner_can_delete_post(app, client, auth):
    auth.register()
    auth.login()
    create_activity(client)

    response = client.post(
        "/delete_post",
        data={"post_id": 1},
        follow_redirects=True,
    )
    assert b"Post deleted" in response.data

    db = database_worker(app.config["DATABASE"])
    post = db.get("SELECT id FROM posts WHERE id = ?", (1,))
    db.close()
    assert post is None


def test_like_is_a_toggle(app, client, auth):
    auth.register()
    auth.login()
    create_activity(client)

    client.post("/post/1/like")
    client.post("/post/1/like")

    db = database_worker(app.config["DATABASE"])
    like_count = db.get(
        "SELECT COUNT(*) FROM likes WHERE post_id = ?",
        (1,),
    )[0]
    stored_count = db.get(
        "SELECT likes FROM posts WHERE id = ?",
        (1,),
    )[0]
    db.close()

    assert like_count == 0
    assert stored_count == 0
