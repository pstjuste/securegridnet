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

    # Run CA tasks
    run_ca_tasks(fb, gid, '0')
    
    return

#==============================================================================
# Task set based on selected mode
#==============================================================================

# This method will run CA tasks
def run_ca_tasks(fb, gid, task):

    # Task 1: Store CA certificate on fb
    if(task == '1' or task == '0'):
        print 'Creating CA certificate'
        create_cert()
        print 'Deleting old certificate from Facebook'
        clean_ca_cert(fb, gid)
        print 'Storing key on Facebook'
        store_ca_cert(fb, gid)
        print 'CA certificate stored successfully'

    # Loop the last two tasks
    while(True) :

        # Task 2: Check for unsigned requests
        unsigned_req_ids = []
        if(task == '2' or task == '0'):
            print 'Checking for certificate request'
            unsigned_req_ids = check_cert_req(fb, gid)
            print 'Checking completed succefully'

        # Task 3: Sign certificates
        if(task == '2' or task == '0'):
            if(len(unsigned_req_ids) > 0):
                print 'Signing certificates'
                get_cert_req(fb, unsigned_req_ids)
                print 'Certificates signed successfully'
            else:
                print 'No certificate requests found'

        # Wait for 60 seconds before checking again with Facebook
        sleep(60)

    return 0

#==============================================================================
# Facebook Certificate Functions (CA)
#==============================================================================

#This method deletes previous CA certificate on Facebook
def clean_ca_cert(fb, gid):

    obj_id = ''

    # Make a Facebook query call to get certificate obj_id
    results = fb.fql.query('SELECT obj_id FROM SecureGridNet.certificate \
              WHERE gid = ' + str(gid) )

    # Get the last result, there should be only one
    for result in results:
        obj_id = result['obj_id']

    # Return if certificate is not found
    if(obj_id == ''):
        return 0

    # Delete the old object id
    common.fb_delete_data(fb, gid, obj_id, 'certificate')

    return 1

# This method stores the CA certificate on Facebook
def store_ca_cert(fb, gid):

    # Get the CA certificate from file system
    cert = common.read_file('demoCA/cacert.pem')

    # Encode certificate for Facebook database
    data = common.fb_encode(cert)

    # Store on Facebook
    common.fb_put_data(fb, gid, data, 'certificate')

    return 0

# This method checks for unsigned certificate requests
def check_cert_req(fb, gid):

    # Get signed certificate ids
    ids_file = common.read_file('signed_cert_ids.txt')

    # Create array of signed ids
    signed_ids = ids_file.split('\n')

    print 'Signed IDs: %s' % (signed_ids)

    # Get list of request ids from Facebook
    results = fb.fql.query('SELECT obj_id FROM SecureGridNet.request \
              WHERE usr_id IN (SELECT uid FROM group_member \
              WHERE gid = ' + str(gid) + ')')

    # Search for unsigned requests
    unsigned_req_ids = []
    for result in results:
        if str(result['obj_id']) not in signed_ids:
            #add to unsigned list
            unsigned_req_ids.append(result['obj_id'])

    print 'Unsigned IDs: %s' % (unsigned_req_ids)

    return unsigned_req_ids

# This method gets unsigned requests from Facebook
def get_cert_req(fb, unsigned_req_ids):

    # Create list of request ids
    req_list = ''
    for item in unsigned_req_ids:
        req_list += str(item) + ','
    req_list = req_list.rstrip(',')

    # Download unsigned requests from Facebook
    results = fb.fql.query('SELECT _id, id, data from SecureGridNet.ipopdata \
              WHERE _id IN (' + req_list + ')')

    # Sign each certificate and store on fb
    for result in results:
        req_id = result['_id']
        req = common.fb_decode(result['data'])

        # Sign certificate and encode for fb
        signed_cert = sign_cert_req(req)
        data = common.fb_encode(signed_cert)

        # Update list of signed ids
        os.system('echo ' + str(req_id) + ' >> signed_cert_ids.txt')

        # Store on Facebook with association to req
        common.fb_put_data(fb, req_id, data, 'certificate')

    return 0

#==============================================================================
# Local Certificate Functions
#==============================================================================

# This method creates certificate if it does not exists
def create_cert():

    # Checks to see if path exists
    if(not os.path.exists('demoCA/cacert.pem')):
        os.system('/usr/lib/ssl/misc/CA.pl -newca')

        # Create blank signed request file
        common.write_file('signed_cert_ids.txt','')

    return 0

# This method signs an unsigned certificate request
# Return a CA-signed certificate
def sign_cert_req(req):

    # Write req to file
    fname = 'tmp_cert_req.pem'
    fname_cert = 'newcert.pem'
    common.write_file(fname, req)

    # Sign the certificate
    os.system('openssl ca -batch -policy policy_anything -key secret \
            -in ' + fname + ' -out ' + fname_cert)

    # Read certificate
    signed_cert = common.read_file(fname_cert)

    return signed_cert

if __name__ == "__main__":
    main()

