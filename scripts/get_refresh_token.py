"""
ONE-TIME helper — run this yourself, once, on your own computer (or Google Cloud Shell),
never in GitHub Actions. It walks you through Google's OAuth consent screen for your
DaadiKeNuske YouTube channel and prints a YT_REFRESH_TOKEN to paste into GitHub Secrets.

Usage:
    pip install google-auth-oauthlib
    python get_refresh_token.py YOUR_CLIENT_ID YOUR_CLIENT_SECRET

It will print a URL — open it in a browser where you are logged into the Google account
that owns/manages the DaadiKeNuske YouTube channel, approve access, then paste the
resulting code back into the terminal.
"""

import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    if len(sys.argv) != 3:
        print("Usage: python get_refresh_token.py CLIENT_ID CLIENT_SECRET")
        sys.exit(1)

    client_id, client_secret = sys.argv[1], sys.argv[2]

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n\n=== SUCCESS ===")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")
    print("\nCopy the value above into your GitHub repo secret named YT_REFRESH_TOKEN.")


if __name__ == "__main__":
    main()
