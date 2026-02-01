import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/contacts.readonly'
]

def get_service():
    if not os.path.exists('token.json'):
        raise FileNotFoundError("token.json not found. Please authenticate first.")
    
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise Exception("Credentials invalid or expired.")
        
        return build('people', 'v1', credentials=creds)
    except Exception as e:
        raise Exception(f"Failed to load credentials: {str(e)}")

def list_contacts(service, max_results=20):
    """
    Lists the user's contacts.
    """
    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=max_results,
        personFields='names,emailAddresses,phoneNumbers,addresses,photos'
    ).execute()
    
    connections = results.get('connections', [])
    contacts_data = []

    for person in connections:
        # Extract Name
        names = person.get('names', [])
        name = names[0].get('displayName') if names else 'Unknown Name'
        
        # Extract Emails
        emails = person.get('emailAddresses', [])
        email_list = [e.get('value') for e in emails]
        primary_email = email_list[0] if email_list else 'No Email'

        # Extract Phones
        phones = person.get('phoneNumbers', [])
        phone_list = [p.get('value') for p in phones]
        primary_phone = phone_list[0] if phone_list else 'No Phone'

        # Extract Address (Locally recorded)
        addresses = person.get('addresses', [])
        address_list = [a.get('formattedValue') for a in addresses]
        primary_address = address_list[0] if address_list else 'Unknown Address'

        # Extract Photo
        photos = person.get('photos', [])
        photo_url = photos[0].get('url') if photos else None

        contacts_data.append({
            'resourceName': person.get('resourceName'), # useful for updates
            'name': name,
            'email': primary_email,
            'emails': email_list,
            'phone': primary_phone,
            'phones': phone_list,
            'address': primary_address,
            'addresses': address_list,
            'photo': photo_url
        })

    return {'status': 'success', 'contacts': contacts_data}

def search_contacts(service, query):
    """
    Searches for contacts based on a query.
    """
    if not query:
        return list_contacts(service)
        
    try:
        results = service.people().searchContacts(
            query=query,
            readMask='names,emailAddresses,phoneNumbers,addresses,photos'
        ).execute()
        
        results_list = results.get('results', [])
        contacts_data = []

        for result in results_list:
            person = result.get('person', {})
            
            # Extract Name
            names = person.get('names', [])
            name = names[0].get('displayName') if names else 'Unknown Name'
            
            # Extract Emails
            emails = person.get('emailAddresses', [])
            email_list = [e.get('value') for e in emails]
            primary_email = email_list[0] if email_list else 'No Email'

            # Extract Phones
            phones = person.get('phoneNumbers', [])
            phone_list = [p.get('value') for p in phones]
            primary_phone = phone_list[0] if phone_list else 'No Phone'

            # Extract Address
            addresses = person.get('addresses', [])
            address_list = [a.get('formattedValue') for a in addresses]
            primary_address = address_list[0] if address_list else 'Unknown Address'

            # Extract Photo
            photos = person.get('photos', [])
            photo_url = photos[0].get('url') if photos else None

            contacts_data.append({
                'resourceName': person.get('resourceName'),
                'name': name,
                'email': primary_email,
                'emails': email_list,
                'phone': primary_phone,
                'phones': phone_list,
                'address': primary_address,
                'addresses': address_list,
                'photo': photo_url
            })

        return {'status': 'success', 'contacts': contacts_data}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
