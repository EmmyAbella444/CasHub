import datetime
import os
import re
import secrets
from functools import wraps
from io import BytesIO
from uuid import uuid4

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from fpdf import FPDF
from werkzeug.utils import secure_filename

from My_library import check_password, database_worker, encrypt_password


app = Flask(__name__)

# Signed Flask sessions replace the original raw user_id cookie.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["DATABASE"] = os.environ.get("CASHUB_DATABASE", "social_net.db")
app.config["UPLOAD_FOLDER"] = os.environ.get(
    "CASHUB_UPLOAD_FOLDER", os.path.join("static", "images")
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
_initialized_database_paths = set()


def get_database_path():
    return app.config["DATABASE"]


def get_upload_folder():
    folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    return folder


def create_database():
    """Create the four tables used by the original CasHub project."""
    database_path = get_database_path()
    db = database_worker(database_path)

    query_user = """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            uname TEXT NOT NULL,
            description TEXT,
            clubs TEXT,
            posts INTEGER DEFAULT 0
        )
    """

    query_post = """
        CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            content TEXT NOT NULL,
            club TEXT,
            datetime TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            picture TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """

    query_comment = """
        CREATE TABLE IF NOT EXISTS comments(
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
        )
    """

    query_likes = """
        CREATE TABLE IF NOT EXISTS likes(
            id INTEGER PRIMARY KEY,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
            UNIQUE(post_id, user_id)
        )
    """

    db.run_save(query_user)
    db.run_save(query_post)
    db.run_save(query_comment)
    db.run_save(query_likes)
    db.close()
    _initialized_database_paths.add(database_path)


@app.before_request
def ensure_database_exists():
    database_path = get_database_path()
    if database_path not in _initialized_database_paths:
        create_database()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def save_uploaded_image(upload):
    """Validate and save an uploaded image, returning its generated filename."""
    if upload is None or not upload.filename:
        return None

    original_name = secure_filename(upload.filename)
    if not original_name or not allowed_image(original_name):
        raise ValueError("Please upload a PNG, JPG, JPEG, GIF, or WEBP image.")

    extension = original_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"
    upload.save(os.path.join(get_upload_folder(), filename))
    return filename


def refresh_post_count(db):
    db.run_save(
        """
        UPDATE users
        SET posts = IFNULL(
            (SELECT COUNT(*) FROM posts WHERE user_id = users.id),
            0
        )
        """
    )


def comments_for_posts(db, posts):
    comments_dict = {}
    for post in posts:
        post_id = post[0]
        comments_dict[post_id] = db.search(
            """
            SELECT comments.content, users.uname
            FROM comments
            INNER JOIN users ON comments.user_id = users.id
            WHERE comments.post_id = ?
            ORDER BY comments.id ASC
            """,
            (post_id,),
        )
    return comments_dict


def post_rows(db, user_id=None):
    query = """
        SELECT
            posts.id,
            posts.title,
            posts.content,
            posts.club,
            posts.likes,
            posts.comments,
            posts.datetime,
            users.uname,
            posts.picture
        FROM posts
        INNER JOIN users ON posts.user_id = users.id
    """
    params = ()

    if user_id is not None:
        query += " WHERE posts.user_id = ?"
        params = (user_id,)

    query += " ORDER BY posts.id DESC"
    return db.search(query, params)


@app.route("/")
@app.route("/index")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    user_id = int(session["user_id"])
    db = database_worker(get_database_path())

    if request.method == "POST":
        title = request.form.get("post-title", "").strip()
        content = request.form.get("post-content", "").strip()
        date_str = request.form.get("date", "").strip()
        clubs = request.form.getlist("clubs[]")
        clubs_str = ", ".join(clubs)

        if not title or not content or not date_str or not clubs:
            db.close()
            flash("Please complete all required post fields.", "error")
            return redirect(url_for("home"))

        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            db.close()
            flash("Please enter a valid activity date.", "error")
            return redirect(url_for("home"))

        upload = request.files.get("file")
        try:
            filename = save_uploaded_image(upload)
        except ValueError as exc:
            db.close()
            flash(str(exc), "error")
            return redirect(url_for("home"))

        db.run_save(
            """
            INSERT INTO posts(title, content, user_id, datetime, club, picture)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                content,
                user_id,
                date_obj.strftime("%Y-%m-%d"),
                clubs_str,
                filename,
            ),
        )
        refresh_post_count(db)
        db.close()

        flash("Activity added.", "success")
        return redirect(url_for("home"))

    posts = post_rows(db)
    comments_dict = comments_for_posts(db, posts)
    db.close()

    return render_template(
        "home.html",
        posts=posts,
        user_id=user_id,
        comments_dict=comments_dict,
    )


@app.route("/post/<int:post_id>/add_comment", methods=["POST"])
@login_required
def add_comment(post_id):
    user_id = int(session["user_id"])
    comment = request.form.get("comment", "").strip()

    if not comment:
        flash("Comment cannot be empty.", "error")
        return redirect(request.referrer or url_for("home"))

    db = database_worker(get_database_path())
    post = db.get("SELECT id FROM posts WHERE id = ?", (post_id,))
    if post is None:
        db.close()
        abort(404)

    db.run_save(
        "INSERT INTO comments(content, user_id, post_id) VALUES (?, ?, ?)",
        (comment, user_id, post_id),
    )
    db.run_save(
        """
        UPDATE posts
        SET comments = (
            SELECT COUNT(*) FROM comments WHERE post_id = ?
        )
        WHERE id = ?
        """,
        (post_id, post_id),
    )
    db.close()

    return redirect(request.referrer or url_for("home"))


@app.route("/post/<int:post_id>/like", methods=["POST"])
@login_required
def like_post(post_id):
    user_id = int(session["user_id"])
    db = database_worker(get_database_path())

    post = db.get("SELECT id FROM posts WHERE id = ?", (post_id,))
    if post is None:
        db.close()
        abort(404)

    user_like = db.get(
        "SELECT id FROM likes WHERE post_id = ? AND user_id = ?",
        (post_id, user_id),
    )

    if user_like:
        db.run_save(
            "DELETE FROM likes WHERE post_id = ? AND user_id = ?",
            (post_id, user_id),
        )
    else:
        db.run_save(
            "INSERT INTO likes(post_id, user_id) VALUES (?, ?)",
            (post_id, user_id),
        )

    likes_count = db.get(
        "SELECT COUNT(*) FROM likes WHERE post_id = ?",
        (post_id,),
    )[0]
    db.run_save(
        "UPDATE posts SET likes = ? WHERE id = ?",
        (likes_count, post_id),
    )
    db.close()

    return redirect(request.referrer or url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        passwd = request.form.get("password", "")

        if not email or not passwd:
            flash("Email and password are required.", "error")
            return render_template("login.html")

        db = database_worker(get_database_path())
        user = db.get(
            "SELECT id, email, password FROM users WHERE email = ?",
            (email,),
        )
        db.close()

        if user and check_password(user_password=passwd, hashed=user[2]):
            session.clear()
            session["user_id"] = user[0]
            return redirect(url_for("home"))

        flash("Incorrect email or password.", "error")

    return render_template("login.html")


password_regex = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        passwd = request.form.get("password", "")
        passwd_check = request.form.get("check_password", "")
        bio = request.form.get("description", "").strip()
        clubs = request.form.getlist("clubs[]")
        clubs_str = ", ".join(clubs)

        if not uname:
            flash("Please enter your name.", "error")
            return render_template("register.html")

        if not re.match(password_regex, passwd):
            flash(
                "Password must be at least 8 characters long and contain "
                "at least one number and one special character.",
                "error",
            )
            return render_template("register.html")

        if not re.match(email_regex, email):
            flash("Please enter a valid email address.", "error")
            return render_template("register.html")

        if passwd != passwd_check:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        db = database_worker(get_database_path())
        existing_user = db.get(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        )

        if existing_user:
            db.close()
            flash("A user with that email already exists.", "error")
            return render_template("register.html")

        db.run_save(
            """
            INSERT INTO users(email, password, uname, description, clubs)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                email,
                encrypt_password(passwd),
                uname,
                bio,
                clubs_str,
            ),
        )
        db.close()

        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/profile")
@app.route("/profile/<int:user_id>")
@login_required
def profile_user(user_id=None):
    # A user can only treat their own page as the editable personal profile.
    user_id = int(session["user_id"])
    db = database_worker(get_database_path())

    user_data = db.get(
        "SELECT uname, email, description, clubs FROM users WHERE id = ?",
        (user_id,),
    )
    posts = post_rows(db, user_id=user_id)
    comments_dict = comments_for_posts(db, posts)
    db.close()

    last_post_date = None
    if posts:
        try:
            last_post_date = datetime.datetime.fromisoformat(posts[0][6])
        except (TypeError, ValueError):
            last_post_date = None

    show_warning = (
        last_post_date is None
        or (datetime.datetime.now() - last_post_date).days > 7
    )

    return render_template(
        "profile.html",
        user=user_id,
        user_id=user_id,
        posts=posts,
        comments_dict=comments_dict,
        user_data=user_data,
        show_warning=show_warning,
    )


@app.route("/statistics")
@login_required
def statistics():
    user_id = int(session["user_id"])
    db = database_worker(get_database_path())

    most_posts_user = db.search(
        """
        SELECT users.uname, COUNT(posts.id) AS post_count
        FROM users
        JOIN posts ON users.id = posts.user_id
        WHERE posts.datetime > date('now', '-7 days')
        GROUP BY users.id
        ORDER BY post_count DESC
        LIMIT 3
        """
    )

    student_stats = db.search(
        """
        SELECT
            users.uname,
            MAX(posts.datetime) AS last_post_time,
            COUNT(posts.id) AS total_posts,
            users.id
        FROM users
        LEFT JOIN posts ON users.id = posts.user_id
        GROUP BY users.id
        ORDER BY
            CASE WHEN last_post_time IS NULL THEN 0 ELSE 1 END,
            last_post_time ASC
        """
    )

    most_posts_clubs = db.search(
        """
        SELECT posts.club, COUNT(posts.id) AS post_count
        FROM posts
        WHERE posts.datetime > date('now', '-7 days')
        GROUP BY posts.club
        ORDER BY post_count DESC
        LIMIT 3
        """
    )

    db.close()

    return render_template(
        "statistics.html",
        most_posts_user=most_posts_user,
        student_stats=student_stats,
        most_posts_clubs=most_posts_clubs,
        user_id=user_id,
    )


def pdf_safe_text(value):
    return str(value or "").encode("latin-1", "replace").decode("latin-1")


@app.route("/save_pdf", methods=["GET"])
@login_required
def save_pdf():
    user_id = int(session["user_id"])
    db = database_worker(get_database_path())
    posts = db.search(
        """
        SELECT title, content, datetime, club, picture
        FROM posts
        WHERE user_id = ?
        ORDER BY datetime DESC, id DESC
        """,
        (user_id,),
    )
    db.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "CasHub Activity Portfolio", ln=1)
    pdf.ln(3)

    if not posts:
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 8, "No activities have been posted yet.")

    for post in posts:
        title, content, activity_date, club, picture = post

        pdf.set_font("Helvetica", "B", 14)
        pdf.multi_cell(0, 8, pdf_safe_text(title))

        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 7, pdf_safe_text(club), ln=1)
        pdf.cell(0, 7, pdf_safe_text(activity_date), ln=1)

        if picture:
            image_path = os.path.join(get_upload_folder(), picture)
            if os.path.exists(image_path):
                try:
                    pdf.image(image_path, w=70)
                    pdf.ln(3)
                except Exception:
                    pass

        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 7, pdf_safe_text(content))
        pdf.ln(7)

    pdf_bytes = bytes(pdf.output())
    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="cashub-portfolio.pdf",
    )


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/delete_post", methods=["POST"])
@login_required
def delete_post():
    user_id = int(session["user_id"])
    post_id = request.form.get("post_id", type=int)

    if post_id is None:
        abort(400)

    db = database_worker(get_database_path())
    post = db.get(
        "SELECT id, picture FROM posts WHERE id = ? AND user_id = ?",
        (post_id, user_id),
    )

    if post is None:
        db.close()
        abort(403)

    db.run_save("DELETE FROM comments WHERE post_id = ?", (post_id,))
    db.run_save("DELETE FROM likes WHERE post_id = ?", (post_id,))
    db.run_save(
        "DELETE FROM posts WHERE id = ? AND user_id = ?",
        (post_id, user_id),
    )
    refresh_post_count(db)
    db.close()

    if post[1]:
        image_path = os.path.join(get_upload_folder(), post[1])
        if os.path.isfile(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass

    flash("Post deleted.", "success")
    return redirect(url_for("profile_user"))


@app.route("/students_profile/<int:user_id>")
@login_required
def students_profile(user_id):
    db = database_worker(get_database_path())

    user_data = db.get(
        "SELECT uname, email, description, clubs FROM users WHERE id = ?",
        (user_id,),
    )
    if user_data is None:
        db.close()
        abort(404)

    posts = post_rows(db, user_id=user_id)
    comments_dict = comments_for_posts(db, posts)
    db.close()

    return render_template(
        "students_profile.html",
        user_data=user_data,
        posts=posts,
        comments_dict=comments_dict,
        user_id=int(session["user_id"]),
    )


if __name__ == "__main__":
    create_database()
    app.run(debug=True)
