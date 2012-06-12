#!/usr/bin/python

from time import sleep
import sys, os, facebook, common

def main():
    
    api_key = 'd33a7f5305f6ff7dd4a603f9049f87f3'
    secret = '2b7b550dea45ccea6ada02b0fafb38c5'

    # Create facebook object
    fb = facebook.Facebook(api_key, secret)

    # Get session information
    fb.session_key = sys.argv[1]
    fb.uid = sys.argv[2]
    gid = sys.argv[3]
    node_type = sys.argv[4]

    # Store type to fileos.system
    common.write_file('type', node_type)

    # Run client tasks
    run_client_tasks(fb, gid, '0')

    return

#==============================================================================
# Task set based on selected mode
#==============================================================================

# This method will run client tasks
def run_client_tasks(fb, gid, task):

    # Task 1: Get CA certificate from Facebook
    if(task == '1' or task == '0') :
        print 'Getting CA certificate from Facebook'
        if(get_ca_cert(fb, gid) == -1):
            print 'CA certificate now found for this group, terminating'
            return

        print 'CA certificate retreived successfully'

    # Task 2: Make certificate request
    if(task == '2' or task == '0'):
        print 'Making certificate request'
        make_cert_request(fb)
        print 'Request made successfully'

    # Loop task 3 until certificate is found
    while(True):

        # Task 3: Check Facebook for certificate
        if(task == '3' or task == '0'):
            print 'Checking Facebook for certificate'
            if(check_cert(fb) == 0):
                print 'Certificate retreived successfully'
                break
            else:
                print 'Certificate not retreived'

        # Wait for 60 seconds before checking Facebook again
        sleep(60)

    # Task 4: Configure IPOP and IPSec
    if(task == '4' or task == '0'):
        print 'Configuring virtual private network'
        configure_ipop(gid)
        configure_ipsec()
        common.write_file('/mnt/fd/fb_done', '')
        print '<h2>Virtual private network configured successfully<h2/>'

    return 0

#==============================================================================
# Facebook Certificate Functions (Client)
#==============================================================================

#This method fetches the group's CA certificate from Facebook
def get_ca_cert(fb, gid):

    # Make a Facebook query call to fetch data
    results = fb.fql.query('SELECT data FROM SecureGridNet.ipopdata \
              WHERE _id IN (SELECT obj_id FROM SecureGridNet.certificate \
              WHERE gid = ' + gid + ')')

    # Get the last result, there should be only one
    for result in results:
        data = result['data']

    # Return if certificate is not found
    if(data == ''):
        return -1

    # Certificate is base64 encoded, so it needs to be decoded
    cert = common.fb_decode(data)

    # Save certificate to floppy image
    common.write_file('/mnt/fd/cacert.pem', cert)

    # Set certificate directory
    rdir = "/etc/racoon/certs"

    # Prepare ca key for racoon
    os.system("cp -f /mnt/fd/cacert.pem " + rdir + "/.")
    os.system("ln -sf " + rdir + "/cacert.pem " + rdir + "/`openssl x509 -noout \
           -hash -in " + rdir + "/cacert.pem`.0")

    return 0

# This method creates a certificate request and stores on facebook
def make_cert_request(fb):

    # Create the necessary request files
    create_req_files()
    
    # Get certificate request
    cert_req = common.read_file('/etc/racoon/certs/newreq.pem')

    # Store request on Facebook
    fb_store_req(fb, cert_req)

    return 0

# This method checks Facebook for certificate
def check_cert(fb):

    # Get object id from file os.system
    obj_id = common.read_file('fb_req_obj_id.txt')

    # Check Facebook for certificate
    results = fb.fql.query('SELECT id, data FROM SecureGridNet.ipopdata \
              WHERE _id IN (SELECT obj_id FROM SecureGridNet.certificate \
              WHERE gid = ' + obj_id + ')')

    # Get result from Facebook database
    id = ''
    data = ''
    for result in results:
        id = result['id']
        data = result['data']

    # Return if certificate is not found
    if(data == ''):
        return -1

    # Check to see if the certificate is for the current user
    if(id != obj_id):
        return -1

    # Decode data to cert
    cert = common.fb_decode(data)

    # Write certificate to file
    common.write_file('/etc/racoon/certs/host-cert.pem', cert)

    return 0

#==============================================================================
# Local Certificate Functions
#==============================================================================

# This method create a certificate request and a host-key
def create_req_files():

    # Set certificate directory
    rdir = "/etc/racoon/certs"

    # Generate key
    os.system("openssl req -new -nodes -newkey rsa:1024 -sha1 -config \
            configs/user_config -keyout " + rdir + "/host-key.pem \
            -out " + rdir + "/newreq.pem")

    return 0

#==============================================================================
# Facebook Helper Functions
#==============================================================================

# This method stores a certificate request on Facebook
def fb_store_req(fb, cert_req):

    # Prepare data for Facebook
    data = common.fb_encode(cert_req)

    # Put data on Facebook
    obj_id = common.fb_put_data(fb, fb.uid, data, 'request')

    # Write object_id to file
    common.write_file('fb_req_obj_id.txt', str(obj_id))

    return 0

#==============================================================================
# Local Helper Functions
#==============================================================================

# This method configures ipsec and racoon
def configure_ipsec():

    # Overwrite racoon config file
    os.system('cp configs/racoon.conf /etc/racoon/racoon.conf')

    # Overwrite ipsec config file
    os.system('cp configs/ipsec-tools.conf /etc/ipsec-tools.conf')
    os.system('chmod 755 /etc/ipsec-tools.conf')

    return 0

# This method creates the ipop configurations files
def configure_ipop(gid):

    # Create files based on user input
    dhcpdata = common.read_file('configs/dhcpdata.conf')
    dhcpdata = dhcpdata.replace('UFGrid00', gid)

    # Files are saved to floppy to maintain compatibility with appliance
    common.write_file('/mnt/fd/dhcpdata.conf', dhcpdata)
    common.write_file('/mnt/fd/ipop_ns', gid)
    common.write_file('/usr/local/ipop/var/ipop_ns', gid)

    # Create ipop config file
    create_ipop_config('/usr/local/ipop/var/ipop.config',gid)

    # Define the type of server created by user
    os.system('cp type /mnt/fd/type')

    # Update the node config file
    os.system('cp /mnt/fd/node.config /usr/local/ipop/var/node.config')

    # Add racoon to ipop restart
    os.system('echo \'/etc/init.d/racoon restart\' >> /etc/init.d/ipop.sh')

    return 0

# This method creates the ipop config file with gid as identifier
def create_ipop_config(path, gid) :
    data = ''
    data += '<IpopConfig>'
    data += '<IpopNamespace>' + gid + '</IpopNamespace>'
    data += '<VirtualNetworkDevice>tapipop</VirtualNetworkDevice>'
    data += '<EnableMulticast>false</EnableMulticast>'
    data += '</IpopConfig>'
    common.write_file(path, data)
    return 0

if __name__ == "__main__":
    main()

