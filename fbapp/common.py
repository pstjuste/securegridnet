
from base64 import encodestring, decodestring

#==============================================================================
# Facebook Helper Functions
#==============================================================================

# Store data on Facebook    
def fb_put_data(fb, identifier, data, assoc_type):
    obj_id = 0
    try:
        obj_id = fb.data.createObject('ipopdata', '{\"id\":\"'+
            str(identifier)+'\",\"data\":\"'+data+'\"}')
        fb.data.setAssociation(assoc_type, identifier, obj_id)
    except:
        print "Facebook put failed"

    return obj_id

# Delete Facebook data
def fb_delete_data(fb, identifier, obj_id, assoc_type):
    fb.data.deleteObject(obj_id)
    fb.data.removeAssociation(assoc_type, identifier, obj_id)
    return 0

# This method prepares data for Facebook database
def fb_encode(input_data):
    output = encodestring(input_data)
    output = output.replace('\n','__')
    return output

# This method decodes Facebook data
def fb_decode(input_data):
    output = input_data.replace('__','\n')
    output = decodestring(output)
    return output

#==============================================================================
# Basic Helper Functions
#==============================================================================

# The method writes data to a file
def write_file(path, data) :
    file_des = open(path, 'w')
    file_des.write(data)
    file_des.close()
    return 0

#This method reads data from a file
def read_file(path) :
    file_des = open(path, 'r')
    data = file_des.read()
    file_des.close()
    return data
