# ear-server-tools

Python script to set the encryption mode for all sites on a Tableau Server. 

# To automate the script fill in these fields

You can find those variables in the script itself:

server: The Tableau Server that you want to change encryption status for

username and password: The username and password of the user to sign in as; Needs to be a Tableau Server admin account in order to change all sites' encryption setting

site_id: Use "" to use the default site; required for login only

target_mode: The encryption mode that all sites should be set to; can be "disabled", "enabled" or "enforced"
