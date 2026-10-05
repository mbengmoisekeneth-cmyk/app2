import hmac
import json
import os
from typing import TypeGuard, cast
from urllib.parse import urlsplit

from flask import Flask, Response, redirect, render_template_string, request


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024

PAGE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bienvenue</title>
  <style>
    :root { color-scheme: light; font-family: "Segoe UI", Arial, sans-serif; }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh; padding: 18px;
      display: grid; place-items: center; background: #f1f3f6; color: #202b38;
    }
    main {
      width: min(100%, 560px); padding: 42px 54px; background: #fff;
      border-radius: 4px; box-shadow: 0 2px 12px #202b3810;
    }
    h1 { margin: 0; font-size: 2.2rem; }
    .subtitle { margin: 12px 0 28px; color: #748398; font-size: 1.05rem; }
    .notice {
      margin-bottom: 24px; padding: 12px; background: #fff4e5;
      color: #704b16; font-size: .9rem; line-height: 1.5;
    }
    label { display: block; margin: 0 0 8px; font-size: .95rem; }
    input {
      width: 100%; min-height: 52px; margin-bottom: 20px; padding: 10px;
      border: 1px solid #d5d9de; border-radius: 2px; font: inherit;
    }
    input:focus { outline: 2px solid #7892ad; outline-offset: 1px; }
    button {
      width: 100%; min-height: 42px; border: 1px solid #aaa; background: #fff;
      color: #d64e55; font: inherit; cursor: pointer;
    }
    button:hover { background: #fff5f5; }
    .error { margin: 0 0 18px; color: #a52228; }
    @media (max-width: 520px) { main { padding: 32px 24px; } }
  </style>
</head>
<body>
  <main>
    <h1>Bienvenue</h1>
    <p class="subtitle">Connectez-vous à votre espace</p>
    <p class="notice">
      Utilisez uniquement votre identifiant et votre code d'accès dédié.
      Ne saisissez pas le mot de passe de votre compte Microsoft ou d'un autre service.
      Le code sert uniquement à vérifier l'accès et n'est pas conservé.
    </p>
    {% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
    <form method="post" action="" autocomplete="off">
      <label for="identifier">Identifiant</label>
      <input id="identifier" name="identifier" type="text" required maxlength="200"
             autocomplete="username">
      <label for="access_code">Code d'accès</label>
      <input id="access_code" name="access_code" type="password" required maxlength="200"
             autocomplete="off">
      <button type="submit">CONNEXION</button>
    </form>
  </main>
</body>
</html>
"""


class ConfigurationError(ValueError):
    pass


def is_string_mapping(value: object) -> TypeGuard[dict[str, str]]:
    if not isinstance(value, dict):
        return False
    entries = cast(dict[object, object], value)
    for key, item in entries.items():
        if not isinstance(key, str) or not isinstance(item, str):
            return False
    return True


def read_configuration() -> tuple[dict[str, str], str]:
    raw_codes = os.environ.get("ACCESS_CODES_JSON", "")
    try:
        parsed_codes: object = json.loads(raw_codes)
    except json.JSONDecodeError as error:
        raise ConfigurationError(
            "ACCESS_CODES_JSON must be a JSON object mapping identifiers to access codes."
        ) from error

    if not is_string_mapping(parsed_codes) or not parsed_codes:
        raise ConfigurationError("ACCESS_CODES_JSON must contain at least one user.")

    normalized_codes: dict[str, str] = {}
    for identifier, access_code in parsed_codes.items():
        if not identifier.strip() or not access_code.strip():
            raise ConfigurationError(
                "Every access-code entry must have a non-empty string identifier and code."
            )
        normalized_identifier = identifier.strip().casefold()
        if normalized_identifier in normalized_codes:
            raise ConfigurationError("User identifiers must be unique, ignoring case.")
        normalized_codes[normalized_identifier] = access_code.strip()

    form_url = os.environ.get("FORM_URL", "").strip()
    parsed_url = urlsplit(form_url)
    if parsed_url.scheme != "https" or not parsed_url.hostname:
        raise ConfigurationError("FORM_URL must be a complete HTTPS URL.")

    return normalized_codes, form_url


def render_page(error: str | None = None, status: int = 200):
    return render_template_string(PAGE, error=error), status


@app.after_request
def add_security_headers(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; style-src 'unsafe-inline'; "
        "form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/")
def index():
    return render_page()


@app.post("/login")
@app.post("/")
def login():
    identifier = request.form.get("identifier", "").strip()
    access_code = request.form.get("access_code", "").strip()
    if not identifier or not access_code:
        return render_page("Saisissez votre identifiant et votre code d'accès.", 400)

    try:
        authorized_codes, form_url = read_configuration()
    except ConfigurationError:
        app.logger.exception("The access-code or form-link configuration is invalid.")
        return render_page(
            "Le service n'est pas configuré correctement. Réessayez plus tard.", 503
        )

    configured_code = authorized_codes.get(identifier.casefold())
    if configured_code is None or not hmac.compare_digest(
        configured_code.encode("utf-8"), access_code.encode("utf-8")
    ):
        return render_page("Identifiant ou code d'accès invalide.", 403)

    return redirect(form_url, code=303)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
