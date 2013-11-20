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
    print '     --mac_en=   Mac english file to use to find other matching keys'
    print '     --win_en=   Windows english file to use to find other matching keys'
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

def readresx(file):
    # Read a .resx and return a map of keys -> strings

    ret = dict()

    dom = ET.parse(file)

    # now iterate over resx entries and fill in
    # They are under root > data
    # <data name="DiscardLines" xml:space="preserve">
    #   <value></value>
    # </data>
    root = dom.getroot()

    for node in root.iter('data'):
        key = node.attrib["name"]

        # value is stored in a subnode called 'value'
        valuenode = node.find("value")

        if valuenode is not None:
            ret[key] = valuenode.text

    return ret


def loadwintomackeyconversion(macfile, winfile):
    # Load the English versions of mac and windows, and match the values up
    # to determine when keys are different
    # We return a mapping from Windows key to Mac key
    ret = dict()

    macdict = readlocalizable(macfile)
    windict = readresx(winfile)

    # we're actually trying to match up the values in order to pick up mismatched keys
    # but early-out if there are matching keys already
    for winkey,winval in windict.iteritems():
        if not winkey in macdict:
            # need to replace Windows '{n}' with %@ to match
            winval = re.sub("\\{\\d\\}", "%@", winval)
            for mackey,macval in macdict.iteritems():
                if winval == macval:
                    ret[winkey] = mackey
                    print "Matched alternative key " + winkey + " -> " + mackey

    return ret





if __name__ == '__main__':
    macfile = None
    resxfile = None
    outputfile = None
    updateExisting = False
    macEnglish = None
    winEnglish = None
    winToMacKeyConversion = None
    
    try:                                
        opts, args = getopt.getopt(sys.argv[1:], "huo:m:w:", ["help", "update", "output=", "mac_en=", "win_en="]) 
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
        elif opt in ("-m", "--mac_en"):
            macEnglish = arg
        elif opt in ("-w", "--win_en"):
            winEnglish = arg


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

    if (macEnglish is not None and winEnglish is not None and \
        os.path.exists(macEnglish) and os.path.exists(winEnglish)):
        winToMacKeyConversion = loadwintomackeyconversion(macEnglish, winEnglish)





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

        if macval is None and winToMacKeyConversion is not None:
            # try to get an alternative key
            mackey = winToMacKeyConversion.get(winkey)
            if mackey is not None:
                macval = macdict.get(mackey)


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
                    winval = winval.replace("%@", "{" + str(replaceidx) + "}", 1)
                    replaceidx += 1

                # replace \n with actual newlines
                winval = winval.replace("\\n", "\n")


                valuenode.text = winval


    resxdom.write(outputfile, encoding="UTF-8",)



    
        
