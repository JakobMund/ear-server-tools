# pylint: disable=C0301
# keep long urls on one line for readabilty
"""
# This script sets an encryption mode for all sites on a server
#
# To run the script, you must have installed Python 2.7.9 or later,
# plus the 'requests' library:
#   http://docs.python-requests.org/en/latest/
#
# Run the script in a terminal window by entering:
#   python set_server_encryption_mode.py <server_address> <username> <encryption_mode>
#
#   You will be prompted for site id
#   See the main() method for details
#
# This script requires a server administrator.
#
# The file version.py must be in the local folder with the correct API version number
"""

import xml.etree.ElementTree as ET # Contains methods used to build and parse XML
import sys
import getpass
import requests # Contains methods used to make HTTP requests
from version import VERSION

# The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0
# or 'http://tableau.com/api' for Tableau Server 9.1 or later
XMLNS = {'t': 'http://tableau.com/api'}

class ApiCallError(Exception):
    """ ApiCallError """
    pass

class UserDefinedFieldError(Exception):
    """ UserDefinedFieldError """
    pass

def _encode_for_display(text):
    """
    Encodes strings so they can display as ASCII in a Windows terminal window.
    This function also encodes strings for processing by xml.etree.ElementTree functions.

    Returns an ASCII-encoded version of the text.
    Unicode characters are converted to ASCII placeholders (for example, "?").
    """
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')

def _check_status(server_response, success_code):
    """
    Checks the server response for possible errors.

    'server_response'       the response received from the server
    'success_code'          the expected success code for the response
    Throws an ApiCallError exception if the API call fails.
    """
    if server_response.status_code != success_code:
        parsed_response = ET.fromstring(server_response.text)

        # Obtain the 3 xml tags from the response: error, summary, and detail tags
        error_element = parsed_response.find('t:error', namespaces=XMLNS)
        summary_element = parsed_response.find('.//t:summary', namespaces=XMLNS)
        detail_element = parsed_response.find('.//t:detail', namespaces=XMLNS)

        # Retrieve the error code, summary, and detail if the response contains them
        code = error_element.get('code', 'unknown') if error_element is not None else 'unknown code'
        summary = summary_element.text if summary_element is not None else 'unknown summary'
        detail = detail_element.text if detail_element is not None else 'unknown detail'
        error_message = '{0}: {1} - {2}'.format(code, summary, detail)
        raise ApiCallError(error_message)
    return

def sign_in(server, username, password, site):
    """
    Signs in to the server specified with the given credentials

    'server'   specified server address
    'username' is the name (not ID) of the user to sign in as.
               Note that most of the functions in this example require that the user
               have server administrator permissions.
    'password' is the password for the user.
    'site'     is the ID (as a string) of the site on the server to sign in to. The
               default is "", which signs in to the default site.
    Returns the authentication token and the site ID.
    """
    url = server + "/api/{0}/auth/signin".format(VERSION)

    # Builds the request
    xml_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(xml_request, 'credentials', name=username, password=password)
    ET.SubElement(credentials_element, 'site', contentUrl=site)
    xml_request = ET.tostring(xml_request)

    # Make the request to server
    server_response = requests.post(url, data=xml_request)
    _check_status(server_response, 200)

    # ASCII encode server response to enable displaying to console
    server_response = _encode_for_display(server_response.text)

    # Reads and parses the response
    parsed_response = ET.fromstring(server_response)

    # Gets the auth token and site ID
    token = parsed_response.find('t:credentials', namespaces=XMLNS).get('token')
    site_id = parsed_response.find('.//t:site', namespaces=XMLNS).get('id')
    # user_id = parsed_response.find('.//t:user', namespaces=XMLNS).get('id')
    return token, site_id

def switch_site(server, auth_token, site):
    url = server + "/api/{0}/auth/switchSite".format(VERSION)

    # Build the request
    xml_request = ET.Element('tsRequest')
    ET.SubElement(xml_request, 'site', contentUrl=site)
    xml_request = ET.tostring(xml_request)

    # Make the request to server
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token}, data=xml_request)
    _check_status(server_response, 200)

    parsed_response = ET.fromstring(_encode_for_display(server_response.text))
    token = parsed_response.find('t:credentials', namespaces=XMLNS).get('token')
    site_id = parsed_response.find('.//t:site', namespaces=XMLNS).get('id')
    return token, site_id

def sign_out(server, auth_token):
    """
    Destroys the active session and invalidates authentication token.

    'server'        specified server address
    'auth_token'    authentication token that grants user access to API calls
    """
    url = server + "/api/{0}/auth/signout".format(VERSION)
    server_response = requests.post(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 204)
    return

def get_group_id(server, auth_token, site_id, group_name):
    """
    Returns the group id for the group name
    """
    url = server + "/api/{0}/sites/{1}/groups".format(VERSION, site_id)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))

    groups = xml_response.findall('.//t:group', namespaces=XMLNS)
    for group in groups:
        if group.get('name') == group_name:
            return group.get('id')
    error = "Group named '{0}' not found.".format(group_name)
    raise LookupError(error)

def query_sites(server, auth_token):
    """
    Queries for all sites on the server
    """
    url = server + "/api/{0}/sites".format(VERSION)
    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    #_check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    sites = xml_response.findall('.//t:site', namespaces=XMLNS)
    return sites

def get_users_in_group(server, auth_token, site_id, group_id, page_size, page_number):
    """
    Get all the users in the group using group id
    GET /api/api-version/sites/site-id/groups/group-id/users
    GET /api/api-version/sites/site-id/groups/group-id/users?pageSize=page-size&pageNumber=page-number
    """
    if page_size == 0:
        url = server + "/api/{0}/sites/{1}/groups/{2}/users".format(VERSION, site_id, group_id)
    else:
        url = server + "/api/{0}/sites/{1}/groups/{2}/users?pageSize={3}&pageNumber={4}".format(VERSION, site_id, group_id, page_size, page_number)

    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    #_check_status(server_response, 200)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    users = xml_response.findall('.//t:user', namespaces=XMLNS)
    return users

def get_site_encryption_mode(server, auth_token, site_id):
    """
    Find out the encryption mode of the site <site_id>
    GET /api/api-version/sites/site_id
    """
    url = server + "/api/{0}/sites/{1}".format(VERSION, site_id)

    server_response = requests.get(url, headers={'x-tableau-auth': auth_token})
    _check_status(server_response, 200);
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    encryption_mode = xml_response.find('.//t:site', namespaces=XMLNS).attrib['extractEncryptionMode']
    return encryption_mode

def set_site_encryption_mode(server, auth_token, site_id, encryption_mode):
    """
    Find out the encryption mode of the site <site_id>
    GET /api/api-version/sites/site_id
    """
    url = server + "/api/{0}/sites/{1}".format(VERSION, site_id)

    xml_request = ET.Element('tsRequest')
    ET.SubElement(xml_request, 'site', extractEncryptionMode=encryption_mode)
    xml_request = ET.tostring(xml_request)

    server_response = requests.put(url, headers={'x-tableau-auth': auth_token}, data=xml_request)
    _check_status(server_response, 200);
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    encryption_mode = xml_response.find('.//t:site', namespaces=XMLNS).attrib['extractEncryptionMode']
    return encryption_mode


def main():
    """
    To automate this script then fill in the values for server, username, etc
    You will be prompted for any values set to ""

    Server and username can be entered on the command line as well.

      set_server_encryption_mode.py http://localhost username

    """
    # To automate the script fill in these fields
    server = "http://jmund-1"
    username = "admin"
    password = "admin"
    site_id = "Default"
    target_mode = "enforced"

    if len(sys.argv) > 2:
        server = sys.argv[1]
        username = sys.argv[2]
        target_mode = sys.argv[3]

    # Prompt for a server - include the http://
    if server == "":
        server = raw_input("\nServer : ")

    # Prompt for a username
    if username == "":
        username = raw_input("\nUser name: ")

    # Prompt for password
    if password == "":
        password = getpass.getpass("Password: ")

    # Prompt for site id
    if site_id == "":
        site_id = raw_input("\nSite name (hit Return for the default site): ")

    # Prompt for target encryption mode
    if target_mode == "":
        target_mode = raw_input("\nEncryption mode to be set for all sites: ")

    # Fix up the site id and group name - blank indicates default value
    if site_id == "Default":
        site_id = ""

    # sign in to server
    auth_token, site_id = sign_in(server, username, password, site_id)

    # get all sites on the server
    sites = query_sites(server, auth_token)

    print("\nSetting encryption mode for all sites on "+server+" to "+target_mode+"\n")

    for site in sites:
        # switch to site (if necessary)
        if (site.get('id') != site_id):
            auth_token, site_id = switch_site(server, auth_token, site.get('contentUrl'))

        site_name = site.get('name')
        encryption_mode = site.get('extractEncryptionMode')

        # update encryption mode (if not already set)
        if encryption_mode != target_mode:
            print(site_name + ": Setting encryption mode from " + encryption_mode + " to " + target_mode)
            set_site_encryption_mode(server, auth_token, site_id, target_mode)
        else:
            print(site_name + ": Encryption mode already set to " + encryption_mode)

    # sign out and invalidate the authentication token
    sign_out(server, auth_token)

if __name__ == "__main__":
    main()