from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.simple import direct_to_template

import facebook.djangofb as facebook
import os, sys, common, threading

# Test function
def test(request):

    return HttpResponse('hello world')

# This is the main entry function for Facebook
def web_app(request):
    response = HttpResponse()

    api_key = 'd33a7f5305f6ff7dd4a603f9049f87f3'
    secret = '2b7b550dea45ccea6ada02b0fafb38c5'

    # Create facebook object
    fb = facebook.Facebook(api_key, secret)

    # Get session information
    fb.session_key = request['fb_sig_session_key']
    fb.uid = request['fb_sig_user']

    form_link = '/fbsample/formsubmit/'

    html = ''

    # Ask user to select group
    groups = fb.fql.query('SELECT gid, name, creator FROM group \
             WHERE gid IN (SELECT gid FROM group_member \
             WHERE uid='+fb.uid+')')

    html += '<h2>IPOP Virtual Private Network Social Web Interface</h2> \
             <h3>Select the group that you will associate to \
             your virtual private network:</h3> \
             <form name=input action=' + form_link + ' method=get>'

    for group in groups:
        html += '<input type=radio name=gid value=\
                ' + str(group['gid']) + ' /> '+ group['name'] + '<br/>'

    html += '<h3>Select the type of Condor node that you would like to run:</h3> \
             <input type=radio name=type value=Server /> \
             Server - Server nodes are the managers <br/> \
             <input type=radio name=type value=Client /> \
             Client - Client nodes are capable of submitting and receiving jobs <br/>\
             <input type=radio name=type value=Worker /> \
             Worker - Worker nodes can only run jobs <br/><br/>\
             <h3>Would you like to run CA node?</h3> <br/>\
             Only group creators will be allowed to run CA nodes. <br/><br/>\
             <input type=radio name=CA value=yes /> Yes <br/>\
             <input type=radio name=CA value=no /> No <br/><br/>\
             <input type=hidden name=session_key value=' + fb.session_key + ' /> \
             <input type=hidden name=uid value='+ str(fb.uid) +' /> \
             <input type=submit name=submit value=Submit /></form>'

    # Send output to web
    response.write(html)

    return response 

# This is a temporary fix, because Facebook loopback always points to same
# address, request is saved to file
def form_submit(request):

    # Check to see if CA node
    if(request['CA'] == 'yes'):

        # Call CA tasks in a seperate thread
        CATaskThread(request['session_key'], request['uid'], 
            request['gid'], request['type']).start()

    else:
        # Call client tasks in a seperate thread
        ClientTaskThread(request['session_key'], request['uid'], 
            request['gid'], request['type']).start()

    # Sends user to status page
    return HttpResponseRedirect('/fbsample/status/')

# Return the status for the output to the user
def status(request):

    response = HttpResponse()

    html = ''

    # Add refresh
    if(not os.path.exists('/mnt/fd/fb_done')):
        html = '<head><meta http-equiv=refresh content=30 ></head>'

    # Add body tags
    html += '<body>'

    # Read status message from file
    html += common.read_file('status.txt')

    # Replace new line with breaks for html processing
    html = html.replace('\n', '<br/>')

    html += '</body>'

    # Send response for webpage
    response.write(html)

    return response

# Thread that runs CA tasks
class CATaskThread (threading.Thread):

    def __init__ (self, session_key, uid, gid, node_type):
        self.session_key = session_key
        self.gid = gid
        self.uid = uid
        self.node_type = node_type
        threading.Thread.__init__(self)

    def run (self):

        os.system('fb_ca_bin/ca_tasks.py '+ self.session_key + ' ' + 
            self.uid + ' ' + self.gid + ' ' + self.node_type +' &> status.txt')
        return    

# Thread that runs client tasks
class ClientTaskThread (threading.Thread):

    def __init__ (self, session_key, uid, gid, node_type):
        self.session_key = session_key
        self.gid = gid
        self.uid = uid
        self.node_type = node_type
        threading.Thread.__init__(self)

    def run (self):

        os.system('fb_client_bin/client_tasks.py '+ self.session_key + ' ' + 
            self.uid + ' ' + self.gid + ' ' + self.node_type +' &> status.txt')
        return    
