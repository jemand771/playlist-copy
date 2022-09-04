import os

import oauthlib.oauth2.rfc6749.errors
import pyyoutube
from flask import Flask, redirect, render_template, request, session

import storage
from model import Job, SourceMode, TargetDupeMode, TargetMode, User, YoutubeApi

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

STORAGE = storage.Storage()


def make_youtube_api():
    return pyyoutube.Api(
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"]
    )


def httpsify_url(url):
    # securr
    if url.startswith("http://"):
        return "https://" + url.removeprefix("http://")
    return url


@app.get("/")
def main_page():
    try:
        get_user_or_send_to_login()
    except UserShouldLogin:
        return render_template("login.html")
    return redirect("/jobs")


class UserShouldLogin(Exception):
    pass


def get_user_or_send_to_login() -> User:
    user_id = session.get("uid")
    if user_id is None:
        raise UserShouldLogin("please log in")
    try:
        user = STORAGE.get_user(user_id)
        user.api.get_user_identifier()
        return user
    except KeyError:
        raise UserShouldLogin("session expired")


@app.errorhandler(UserShouldLogin)
def send_to_login_page(e):
    print("handling login exception", e)
    del session["uid"]
    return redirect("/")


@app.get("/logout")
def forced_logout():
    raise UserShouldLogin("successfully logged out")


@app.get("/auth/youtube")
def youtube_signin():
    auth_url, state = make_youtube_api().get_authorization_url(httpsify_url(request.host_url + "authcb/youtube"))
    auth_url = auth_url.replace("select_account", "consent")
    print(auth_url)
    return redirect(auth_url)


@app.get("/authcb/youtube")
def youtube_signing_callback():
    api = make_youtube_api()
    try:
        api.generate_access_token(
            authorization_response=httpsify_url(request.url),
            redirect_uri=httpsify_url(request.host_url + "authcb/youtube")
        )
    except oauthlib.oauth2.rfc6749.errors.AccessDeniedError:
        raise UserShouldLogin("oauth flow cancelled or missing scopes")

    yt_api = YoutubeApi(api)
    user_id = yt_api.get_user_identifier()
    if STORAGE.user_exists(user_id):
        user = STORAGE.get_user(user_id)
        user.api = yt_api
    else:
        user = User(id=user_id, type="youtube", api=yt_api)

    STORAGE.update_user(user)
    session["uid"] = user_id
    return redirect("/jobs")


@app.get("/jobs")
def job_list():
    user = get_user_or_send_to_login()
    print("authorized user accessing job list:", user.api.get_user_identifier())
    return render_template("joblist.html", user=user)


@app.get("/edit/<job_id>")
def edit_job(job_id):
    user = get_user_or_send_to_login()
    job = None
    for _job in user.jobs:
        if _job.id == job_id:
            job = _job
            break
    if job is None:
        return "invalid job id"
    new = "new" in request.args
    return render_template(
        "jobedit.html",
        job=job,
        new=new,
        SourceMode=SourceMode,
        TargetMode=TargetMode,
        TargetDupeMode=TargetDupeMode
    )


@app.post("/edit/<job_id>")
def edit_job_post(job_id):
    user = get_user_or_send_to_login()
    job = user.get_job(job_id)
    job.name = request.form.get("name")
    job.source = request.form.get("source")
    job.target = request.form.get("target")
    job.src_mode = SourceMode(int(request.form.get("src_mode")))
    job.target_mode = TargetMode(int(request.form.get("target_mode")))
    job.target_dupe_mode = TargetDupeMode(int(request.form.get("target_dupe_mode")))
    job.treat_seen_as_dupes = "treat_seen_as_dupes" in request.form
    job.purge_before_operation = "purge_before_operation" in request.form
    job.reverse_source = "reverse_source" in request.form
    STORAGE.update_user(user)
    return redirect("/jobs")


@app.get("/new")
def new_job():
    user = get_user_or_send_to_login()
    job = Job(src_mode=SourceMode.none, target_mode=TargetMode.create, name="new job lol")
    user.jobs.append(job)
    STORAGE.update_user(user)
    return redirect(f"/edit/{job.id}?new=1")


@app.get("/delete/<job_id>")
def delete_job(job_id):
    user = get_user_or_send_to_login()
    for job in user.jobs:
        if job.id == job_id:
            user.jobs.remove(job)
            STORAGE.update_user(user)
            return redirect("/jobs")
    return "invalid job id"


# throw error on startup if yt api credentials are invalid
make_youtube_api()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
