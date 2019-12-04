# ear-server-tools

Python script to set the encryption mode for all sites on a Tableau Server. 

# Usage

When running the script, the user will be prompted for the server, username, password, and the encryption mode that all sites will be set to. Alternatively, to avoid being prompted/automate the script, set default values for those variables in the script itself:

server: The Tableau Server that you want to change encryption status for

username and password: The username and password of the user to sign in as; Needs to be a Tableau Server admin account in order to change all sites' encryption setting

target_mode: The encryption mode that all sites should be set to; can be "disabled", "enabled" or "enforced"
