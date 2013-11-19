#!/usr/bin/env python

import sys
import os
import getopt
import xml.etree.cElementTree as ET
import re
import codecs

def usage():
    print 'Usage:'
    print '  convert_trans.py [--update] [--output=resxfile] macfile resxfile'
    print ''
    print '     --update    Overwrite existing strings in the output'
    print '                 (The default is to only complete new strings)'
    print '     --output=   Write result to given file instead of resx.out'
    print '     macfile     A Mac localisation file (Localizable.strings)'
    print '     resxfile    An existing .resx file to port translations to'
    print '  NOTE: if you want to call without "python" prefix, make sure'
    print '        you read http://stackoverflow.com/a/2641185'
    print ''

def readlocalizable(file):
    # read a Localizable.strings style file and read all strings into a dictionary
    f = codecs.open(file, "r", encoding="UTF-8")

    # compile regex to parse out "key" = "string" statements
    regex = re.compile("\"([^\"]+)\"\\s*=\\s*\"([^\"]+)\"")

    ret = dict()

    for line in f:
        match = regex.match(line)
        if match:
            captures = match.groups()
            if (len(captures) == 2):
                ret[captures[0]] = captures[1]

    return ret




if __name__ == '__main__':
    macfile = None
    resxfile = None
    outputfile = None
    updateExisting = False
    
    try:                                
        opts, args = getopt.getopt(sys.argv[1:], "huo:", ["help", "update", "output"]) 
    except getopt.GetoptError, err: 
        print str(err)
        usage()                          
        sys.exit(2)
    
    for opt, arg in opts:    
        if opt in ("-h", "--help"):      
            usage()                     
            sys.exit()                  
        elif opt in ("-u", "--update"): 
            updateExisting = True
        elif opt in ("-o", "--output"):
            outputfile = arg


    #print opts

    if (len(args) != 2):
        usage()
        sys.exit(5)

    macfile = "".join(args[0])
    resxfile = "".join(args[1])

    if (outputfile is None):
        outputfile = resxfile + ".out"

    print "mac file is " + macfile
    print "resx file is " + resxfile

    if (macfile is None or len(macfile) == 0 or not os.path.exists(macfile)):
        print "Mac file invalid"
        usage()
        sys.exit(5)

    if (resxfile is None or len(resxfile) == 0 or not os.path.exists(resxfile)):
        print "Resx file invalid"
        usage()
        sys.exit(5)

    # open target resx
    resxdom = ET.parse(resxfile)

    # open mac strings and convert to dictionary
    macdict = readlocalizable(macfile)


    # now iterate over resx entries and fill in
    # They are under root > data
    # <data name="DiscardLines" xml:space="preserve">
    #   <value></value>
    # </data>
    root = resxdom.getroot()

    for node in root.iter('data'):
        # try to find a matching key in the mac file
        winkey = node.attrib["name"]
        #print "Looking for string for: " + winkey
        macval = macdict.get(winkey)

        if macval is not None and len(macval) > 0:
            #print "Found string: " + macval

            # value is stored in a subnode called 'value'
            valuenode = node.find("value")

            if updateExisting or valuenode.text is None or len(valuenode.text) == 0:
                # Found the string on Mac
                # Deal with argument placeholders: %@ on Mac, {0}, {1} in resx
                winval = macval
                replaceidx = 0;
                while winval.find("%@") != -1:
                    winval = winval.replace("%@", "{" + str(replaceidx) + "}")
                    replaceidx = replaceidx + 1

                # replace \n with actual newlines
                winval = winval.replace("\\n", "\n")


                valuenode.text = winval


    resxdom.write(outputfile, encoding="UTF-8",)



    
        
