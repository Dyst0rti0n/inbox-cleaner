import argparse
import os.path
import re
import base64
import json
import webbrowser
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

UNSUB_FILE = 'unsubscribed.json'

def authenticate(creds_path='credentials.json', token_path='token.json'):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def list_subscriptions(service, query: str = 'unsubscribe', max_results: int = 100, include_unsubscribed: bool = False):
    unsubscribed = get_unsubscribed()
    blocked = get_blocked_addresses(service)

    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages', [])
    subs = []

    for msg in messages:
        msg_detail = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject', 'List-Unsubscribe']
        ).execute()

        headers = {
            h['name']: h['value']
            for h in msg_detail.get('payload', {}).get('headers', [])
        }

        sender = headers.get('From', '')
        match = re.search(r'<([^>]+)>', sender)
        email = match.group(1).lower() if match else sender.lower()

        if any(blocked_email in email for blocked_email in blocked):
            continue
        already_unsub = email in unsubscribed
        if already_unsub and not include_unsubscribed:
            continue

        subs.append({
            'id': msg['id'],
            'from': sender,
            'subject': headers.get('Subject', ''),
            'unsubscribe': headers.get('List-Unsubscribe', ''),
            'already_unsub': already_unsub
        })

    return subs

def delete_messages_from(service, addresses):
    to_delete = []
    for address in addresses:
        query = f'from:{address}'
        page_token = None
        while True:
            results = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
            messages = results.get('messages', [])
            if not messages:
                break
            to_delete.extend([m['id'] for m in messages])
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        if to_delete:
            service.users().messages().batchDelete(userId='me', body={'ids': to_delete}).execute()
            print(f"Deleted {len(to_delete)} messages from {address}")
        else:
            print(f"No messages found from {address}")

def delete_message(service, message_id):
    service.users().messages().delete(userId='me', id=message_id).execute()
    print(f"Deleted message: {message_id}")

def send_email(service, to, subject, body):
    msg = EmailMessage()
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': encoded}).execute()

def send_unsubscribe(service, header):
    for part in re.findall(r'<([^>]+)>', header):
        if part.startswith('mailto:'):
            address = part[len('mailto:'):]
            send_email(service, address, 'Unsubscribe', 'Please unsubscribe me from this list.')
            print(f"Sent unsubscribe email to {address}")
            return
        if part.startswith('http'):
            webbrowser.open(part)
            print(f"Opened unsubscribe link: {part}")
            return
    print(f"No actionable unsubscribe method found.")

def create_block_filter(service, address):
    body = {
        'criteria': {
            'from': address
        },
        'action': {
            'addLabelIds': ['TRASH']
        },
    }
    service.users().settings().filters().create(userId='me', body=body).execute()
    print(f"Created filter to trash future emails from {address}")

def interactive_client(service, query='unsubscribe'):
    subs = list_subscriptions(service, query)
    for idx, sub in enumerate(subs, 1):
        print(f"\n[{idx}] {sub['from']} - {sub['subject']}")
        if sub['unsubscribe']:
            print(f" Unsubscribe header: {sub['unsubscribe']}")
        action = input("Choose action ([d]elete, [u]nsubscribe, [b]lock, [s]kip)").strip().lower()
        if action == 'd':
            delete_message(service, sub['id'])
        elif action == 'u':
            send_unsubscribe(service, sub['unsubscribe'])
        elif action == 'b':
            match = re.search(r'<([^>]+)>', sub['from'])
            addr = match.group(1) if match else sub['from']
            create_block_filter(service, addr)
        else:
            print("Skipped.")

def extract_user_id(service):
    profile = service.users().getProfile(userId='me').execute()
    return profile['emailAddress'].split('@')[0]

def get_blocked_addresses(service):
    result = service.users().settings().filters().list(userId='me').execute()
    filters = result.get('filter', [])
    blocked = []
    for f in filters:
        criteria = f.get('criteria', {})
        action = f.get('action', {})
        if action.get('addLabelIds') == ['TRASH'] and 'from' in criteria:
            blocked.append(criteria['from'].lower())
    return blocked

def save_unsubscribed(email):
    try:
        with open(UNSUB_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    if email not in data:
        data.append(email)
        with open(UNSUB_FILE, 'w') as f:
            json.dump(data, f)
    print(f"Added {email} to unsubscribed list")

def get_unsubscribed():
    try:
        with open(UNSUB_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def main():
    parser = argparse.ArgumentParser(description='Email Cleaner')
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_list = subparsers.add_parser('list', help='List potential subscription emails')
    parser_list.add_argument('--query', type=str, default='unsubscribe', help='Search query for potential subscriptions')

    parser_delete = subparsers.add_parser('delete', help='Delete all messages from a query or address')
    parser_delete.add_argument('--address', help='Delete emails matching from this address')
    parser_delete.add_argument('--query', help='Delete messages matching this Gmail search query')

    parser_block = subparsers.add_parser('block', help='Create a filter to move future emails from an address to bin')
    parser_block.add_argument('--address', required=True, help='Address to block')

    parser_interactive = subparsers.add_parser('interactive', help='Interactively clean subscription emails')
    parser_interactive.add_argument('--query', default='unsubscribe', help='Search query for subscriptions')

    args = parser.parse_args()
    service = authenticate()
    user_id = extract_user_id(service)

    if args.command == 'list':
        subs = list_subscriptions(service, args.query)
        output_lines = []
        for sub in subs:
            sender = sub['from']
            match = re.match(r'(?:"?([^"]+)"?\s)?<?(.+@[^>]+)>?', sender)
            brand = match.group(1) if match and match.group(1) else match.group(2).split('@')[0] if match else sender

            unsub_links = re.findall(r'<(.*?)>', sub['unsubscribe'])
            primary_unsub = ""
            for link in unsub_links:
                if link.startswith('http'):
                    primary_unsub = f'Unsubscribe: {link}'
                    break
                elif link.startswith('mailto:') and not primary_unsub:
                    primary_unsub = f'Unsubscribe: {link}'

            output_lines.append(f"Brand: {brand}")
            output_lines.append(f"Subject: {sub['subject']}")
            output_lines.append(f"{primary_unsub if primary_unsub else 'Unsubscribe: Not found'}\n")

        output_text = "\n".join(output_lines)
        print(output_text)

        with open(f"subscriptions_{user_id}.txt", "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"\n✅ Saved to subscriptions_{user_id}.txt")

    elif args.command == 'delete':
        if args.address:
            delete_messages_from(service, [args.address])
        elif args.query:
            delete_messages_from(service, [args.query])
        else:
            print("You must specify --address or --query for delete")
    elif args.command == 'block':
        create_block_filter(service, args.address)
    elif args.command == 'interactive':
        interactive_client(service, args.query)

if __name__ == '__main__':
    main()
