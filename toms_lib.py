#!/usr/bin/python3
# name: sentry_lib.py
# version: 0.3 
# date: July 2016


def captureTestImage(test_width, test_height, logfile, tidy_list,  camera_timeout, verbose):

    import subprocess
    import time
    from io import BytesIO 
    from PIL import Image
 
    sleeptime = 300

    command = "raspistill -w %s -h %s -t 1 -e bmp -o -" % (test_width, test_height)
    imageData = BytesIO()

    if verbose:
        datestr = get_date()
        message = "INFO: now taking sample image by executing command " + command + " camera_timeout = " + str(camera_timeout) + " at " + datestr  + "\n"
        update_file (message, logfile)

    try:
        imageData.write(subprocess.check_output(command,timeout=camera_timeout,shell=True))

    except subprocess.TimeoutExpired:
         datestr = get_date()
         message = "ERROR: test image capture ran for longer than timeout " + str(camera_timeout) + " at " + datestr  + "\n"
         update_file (message, logfile)

         update_file("INFO: Now sleeping for %s seconds before rebooting at %s \n" % (str(sleeptime), datestr), logfile)
         time.sleep(sleeptime)

         update_file("INFO: Now rebooting at %s \n" % (datestr), logfile)
         tidy_flagfiles(tidy_list, logfile)
         system_shutdown(logfile,restart=True)

    except subprocess.CalledProcessError:
         datestr = get_date()
         message = "ERROR: test image capture returned a non-zero exit status at " + datestr  + "\n"
         update_file (message, logfile)

         update_file("INFO: Now sleeping for %s seconds before rebooting at %s \n" % (str(sleeptime), datestr), logfile)
         time.sleep(sleeptime)

         update_file("INFO: Now rebooting at %s \n" % (datestr), logfile)
         tidy_flagfiles(tidy_list, logfile)
         system_shutdown(logfile,restart=True)

    except:
         datestr = get_date()
         message = "ERROR: test image capture returned an un-caught error at " + datestr  + "\n"
         update_file (message, logfile)

         update_file("INFO: Now sleeping for %s seconds before rebooting at %s \n" % (str(sleeptime), datestr), logfile)
         time.sleep(sleeptime)

         update_file("INFO: Now rebooting at %s \n" % (datestr), logfile)
         tidy_flagfiles(tidy_list, logfile)

    if verbose:
        datestr = get_date()
        message = "INFO: sample image captured OK at " + datestr  + "\n"
        update_file (message, logfile)

    imageData.seek(0)
    im = Image.open(imageData)
    buffer = im.load()
    imageData.close()

    return im, buffer


def detect_motion(film_enable, film_width, film_height, film_duration,photo_width, photo_height,test_width, test_height, pct_quality, filepath, filenamePrefix, logfile, email_alert_user, sensitivity, threshold, verbose, tidy_list, camera_timeout):

     import os
     from datetime import datetime

     if verbose:
         datestr = get_date()
         message = "INFO: now executing motion detection routine at " + datestr  + "\n"
         update_file (message, logfile)

     t1 = datetime.now()
     # Get first image
     image1, buffer1 = captureTestImage(test_width, test_height, logfile, tidy_list, camera_timeout, verbose)

     t2 = datetime.now()
     # Get comparison image
     image2, buffer2 = captureTestImage(test_width, test_height, logfile, tidy_list, camera_timeout, verbose)

     t3 = datetime.now()
     changedPixels = 0
     for x in range(0, test_width):
         # Scan one line of image then check sensitivity for movement
         for y in range(0, test_height):
             # Check green as it's the highest quality channel
             pixdiff = abs(buffer1[x, y][1] - buffer2[x, y][1])
             if pixdiff > threshold:
                 changedPixels += 1

                 if changedPixels > sensitivity:
                      if film_enable:
                          filename = saveFilm(film_width, film_height, filepath, logfile, film_duration)

                      else:
                          filename = saveImage(photo_width, photo_height, pct_quality, filepath, filenamePrefix, logfile)

                      return (filename) 

     t4 = datetime.now()

     if verbose:

         elapsed_time1 = str((t2 - t1).total_seconds())
         elapsed_time2 = str((t3 - t2).total_seconds())
         elapsed_time3 = str((t4 - t3).total_seconds())
         datestr = get_date()
         message = "INFO: image1 capture took " + elapsed_time1 + " Secs, image2 capture took " + elapsed_time2 + " Secs, image processing took " + elapsed_time3 +  " Secs at " + datestr + "\n"
         update_file (message, logfile)



     return('')

def saveFilm(film_width, film_height, filepath, logfile, film_duration):

    import subprocess
    import os

    datestr = get_date()

    temp_filename = filepath + "/film_" + str(film_width) + "x" + str(film_height) + "_" + datestr + ".h264"
    filename = filepath + "/film_" + str(film_width) + "x" + str(film_height) + "_" + datestr + ".mp4"

    subprocess.call("raspivid -fps 30 -mm matrix -w %d -h %d -o %s -t %d" % (film_width, film_height, temp_filename, film_duration), shell=True)
    subprocess.call("MP4Box -fps 30 -add %s %s > /dev/null 2>&1" % (temp_filename,filename), shell=True) 
    os.remove (temp_filename)

    update_file("INFO: Captured film %s at %s \n" % (filename,datestr), logfile)

    return (filename)


def saveImage(photo_width, photo_height, pct_quality, filepath, filenamePrefix, logfile):

    import subprocess
    datestr = get_date()
    filename = filepath + "/" + filenamePrefix + "_" + str(photo_width) + "x" + str(photo_height) + "_" + datestr + ".jpg"
    subprocess.call("raspistill -mm matrix -w %d -h %d -e jpg -q %d -o %s" % (photo_width, photo_height, pct_quality, filename), shell=True)

    update_file("INFO: Captured %s at %s \n" % (filename,datestr), logfile)

    return (filename)

def tidy_flagfiles(tidy_list,logfile):	# remove all files in tidy_list if they exist
    import os
    datestr = get_date()
    for f in tidy_list:
        if os.path.isfile(f):
            update_file("INFO: removing file %s at %s \n" % (f,datestr), logfile)
            os.remove(f)
        else:
            update_file("INFO: will not remove file %s as it does not exist at %s \n" % (f,datestr), logfile)


def sendEmail(emailTo,emailSubject, email_user, email_server, email_password, logfile, filename='',first_line=''):

    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    from email.mime.text import MIMEText
    import imaplib
    import os

    datestr = get_date()
    # Create the container (outer) email message
    msg = MIMEMultipart()
    msg['Subject'] = emailSubject + ' ' +  datestr
    msg['From'] = email_user
    msg['To'] = emailTo

    if first_line:
        msg.attach(MIMEText(first_line))

    if filename:
        if ('.jpg' in filename.lower()) or ('.bmp' in filename.lower()): # if an image file is being attached 
          with open(filename,'rb') as f:
            img = MIMEImage(f.read(), name=os.path.basename(filename))
            msg.attach(img)
        elif ('.mp4' in filename.lower()) : # this is a movie file alert
            # do nothing
            pass
        else:
          with open (filename, 'r') as f:
            attachment = MIMEText(f.read())
            msg.attach(attachment)


    # Send the email via the SMTP server
    datestr = get_date()
    try:
       smtp = smtplib.SMTP(email_server)
       smtp.login(email_user, email_password)
       smtp.sendmail(email_user, emailTo, msg.as_string())
       update_file("INFO: email response sent to " + emailTo + " at: " + datestr + "\n", logfile)

    except smtplib.SMTPException:
       update_file("ERROR: unable to send email response to " + emailTo + " at: " + datestr + "\n", logfile)

def accessPermitted(senderAddress, acl, use_acl):  # return true if senderAddress in ACL list
    if use_acl:			# check access control list for SenderAddress 
       check = False
       for a in acl:
          if (a == senderAddress):
             check = True
             break
    else:			# ignore ACL and return true
       check = True

    return (check)

def getEmailInfo(response_part):

    import email
    msg = email.message_from_bytes(response_part[1])
    varSubject = msg['subject']
    varFrom = msg['from']

    #remove the brackets around the sender email address
    varFrom = varFrom.replace('<', '')
    varFrom = varFrom.replace('>', '')

    # address = last element from list
    senderAddress =  varFrom.split()[-1]

    # truncate with (...) if subject length is greater than 35 characters
    if len( varSubject ) > 35:
        varSubject = varSubject[0:32] + '...'

    return (senderAddress, varSubject)

def processEmail(email_server, email_user, email_password, logfile, keepalive_file, acl, use_acl, emailSubject, verbose, stopfile, tidy_list, photo_width, photo_height, pct_quality, filepath, filenamePrefix):

    import smtplib
    import imaplib
    import os
    import sys
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    from email.mime.text import MIMEText

    if verbose:
        datestr = get_date()
        message = "INFO: now executing processEmail function at " + datestr + "\n"
        update_file (message, logfile)

    try: 
        m = imaplib.IMAP4_SSL(email_server)
    except:
        datestr = get_date()
        update_file("ERROR: failed to create IMAP_SSL object for email server %s at %s \n" % (email_server,datestr), logfile)
        return (False)

    try:
        rv, data = m.login(email_user, email_password)
    except imaplib.IMAP4.error:
        datestr = get_date()
        update_file("ERROR: IMAP login to %s as %s failed at %s \n" % (email_server,email_user,datestr), logfile)
        return (False)

    m.select('inbox')
    typ, data = m.search(None, "UNSEEN")
    ids = data[0]
    id_list = ids.split()

    # if any new emails have arrived
    if id_list:

        for i in id_list: # for each new email

            typ, data = m.fetch( i, '(RFC822)' )

            for response_part in data: # for each part of the email

                if isinstance(response_part, tuple):	# if the part is a tuple then read email info

                    senderAddress, varSubject = getEmailInfo (response_part)
                    
                    if verbose:
                        datestr = get_date()
                        update_file("INFO: email received from %s, subject = %s,  at %s \n" % (senderAddress, varSubject, datestr), logfile)

                    if accessPermitted(senderAddress, acl, use_acl):

                        if 'cammy:logs' in varSubject.lower(): # logfile requested
                            datestr = get_date()
                            update_file("INFO: A copy of the logfile was requested by %s at %s \n" % (senderAddress, datestr), logfile)
                            sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, logfile,"Here is a copy of the logfile contents:\n")

                        elif 'cammy:help' in varSubject.lower(): # helprequested
                            datestr = get_date()
                            helpMessage = "Help contents - include the following in email subject heading: \n\
cammy:logs \t\t sends the logfile contents\n\
cammy:resetlogs \t resets the logfile\n\
cammy:shutdown \t shuts down the system\n\
cammy:stop \t\t keeps polling for emails but stops motion detection\n\
cammy:resume \t\t will resume motion detection\n\
cammy:restert \t\t will shut down the system for keeps\n\
cammy:help \t\t will email this message back!"
                            sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile,'',helpMessage)

                        elif 'cammy:resetlogs' in varSubject.lower(): # logfile reset requested
                            os.remove (logfile)
                            os.remove (keepalive_file)
                            datestr = get_date()
                            update_file("INFO: A logfile reset was requested by %s at %s \n" % (senderAddress, datestr), logfile)
                            sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, logfile,"The logfile has been reset, here is the new logfile contents:\n")


                        elif 'cammy:shutdown' in varSubject.lower(): # shutdown requested
                            datestr = get_date()
                            update_file("INFO: A shutdown was requested by %s at %s \n" % (senderAddress, datestr), logfile)
                            sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, '',"Your request to shut down the system has been actioned\n")
                            tidy_flagfiles(tidy_list, logfile)
                            system_shutdown(logfile,restart=False)

                        elif 'cammy:stop' in varSubject.lower(): # request to stop monitoring 
                            datestr = get_date()
                            update_file("INFO: A request to stop monitoring was made by %s at %s \n" % (senderAddress, datestr), logfile)

                            if (not os.path.isfile(stopfile)):
                                open(stopfile, 'a').close()  # create stop file
                                sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, '',"Your request to stop detecting motion has been actioned\n")

                            else:
                                sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, '',"Your request to stop detecting motion has not been actioned since it was already stopped\n")

                        elif 'cammy:resume' in varSubject.lower(): # request to resume monitoring 
                            datestr = get_date()
                            update_file("INFO: A request to resume monitoring was made by %s at %s \n" % (senderAddress, datestr), logfile)

                            if os.path.isfile(stopfile):
                                os.remove(stopfile)
                                sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, '',"Your request to resume detecting motion has been actioned\n")

                            else:
                                sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, '',"Your request to resume detecting motion has not been actioned as it was not stopped\n")

                        elif 'cammy:restart' in varSubject.lower(): # shutdown requested
                            datestr = get_date()
                            update_file("INFO: A reboot was requested by %s at %s \n" % (senderAddress, datestr), logfile)
                            sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, '',"Your request to reboot the system has been actioned\n")
                            tidy_flagfiles(tidy_list, logfile)
                            system_shutdown(logfile,restart=True)

                        else:
                            filename = saveImage (photo_width, photo_height, pct_quality, filepath, filenamePrefix, logfile)
                            sendEmail (senderAddress, emailSubject, email_user, email_server, email_password, logfile, filename,"A standard image photo was requested - please find the attached image\n")
                            os.remove (filename)

                    else:
                        datestr = get_date()
                        update_file("WARN: Email address %s not recognised at %s \n" % (senderAddress,datestr), logfile)

        m.logout()
    return (True)






def checkIP(IPaddress): #return true if IP address pings OK
    import os
    import subprocess
    with open(os.devnull, 'w') as fNull:
      response = False
      res = subprocess.call(['ping', '-q','-c', '1', IPaddress],stdout=fNull, stderr=fNull)

    if res == 0:
        response = True

    return (response)


def checkNetworks(nw_checks, logfile):  # return true if all network interfaces ping OK
    check = True
    for i in nw_checks:
      if not checkIP(i):
        datestr = get_date()
        update_file("WARN: Failed to contact network address %s at %s \n" % (i, datestr), logfile)
        check = False
        break

    return (check)

def get_date(): # return current date and time
        from datetime import datetime
        time = datetime.now()
        return "%02d-%02d-%04d_%02d%02d%02d" % (time.day, time.month, time.year, time.hour, time.minute, time.second)

def update_file(message,filename): # append filename with message
    with open(filename,'a') as f:
        f.write(message)

def representsInt(s):
    try:
        int(s)
        return True

    except ValueError:
        return False

def get_num_file(filename):
    import os
    if os.path.isfile(filename):

        with open(filename, 'r') as f:
            firstLine = f.readline()

        firstList = firstLine.split()
        firstNum = firstList[0]

        if representsInt(firstNum):
            firstInt = int(firstNum)

        else:          # return a default of 0 if no integer value detected
            firstInt = 0

        return firstInt 


def system_shutdown(logfile,restart):
    if restart is True:
        command = "/usr/bin/sudo /sbin/shutdown -r now"

    else:
        command = "/usr/bin/sudo /sbin/shutdown -h now"

    message = "Now issuing command " + command + "\n"
    update_file (message, logfile)

    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]


def dropbox_upload(verbose,logfile,appname,token,uploadfile,dropbox_folder):
    
  if verbose:
    message = "INFO: using appname = " + appname + " to upload to Dropbox\n"
    update_file (message, logfile)

  import dropbox
  import os.path
  from dropbox.exceptions import ApiError, AuthError
  from dropbox.files import WriteMode

  dbx = dropbox.Dropbox(token)

  try:
    dbx.users_get_current_account()
    if os.path.isfile(uploadfile):
      with open(uploadfile, 'rb') as f:

        filename = dropbox_folder + os.path.basename(uploadfile)
        if verbose:
            message = "INFO: filename =  " + filename + " uploadfile = " + uploadfile +  " \n"
            update_file (message, logfile)

        try:
            dbx.files_upload(f.read(), filename, mode=WriteMode('overwrite'))
            message = "INFO: successfully uploaded file " + uploadfile + " as " + filename + " to Dropbox within application " + appname + " \n"
            update_file (message, logfile)

        except ApiError as err:
            message = "ERROR: an error ocurred attemping to upload file to dropbox\n"
            update_file (message, logfile)

    else:
      message = "ERROR: filename " + uploadfile + " does not exist hence not uploading to Dropbox\n"
      update_file (message, logfile)

  except AuthError as err:
    message = "ERROR: Invalid Dropbox access token\n"
    update_file (message, logfile)


def dropbox_cleanup(verbose,logfile,appname,token,dropbox_folder,dropbox_keep_files):
    
  if verbose:
    message = "INFO: using appname = " + appname + " to cleanup Dropbox\n"
    update_file (message, logfile)

  import dropbox
  import os.path
  from dropbox.exceptions import ApiError, AuthError
  from dropbox.files import WriteMode

  dbx = dropbox.Dropbox(token)
  file_list = dbx.files_list_folder(dropbox_folder).entries

  counter = 0
  num_files = len(file_list)
  counter_threshold = num_files - dropbox_keep_files

  while counter < num_files:

      if counter < counter_threshold:
          delfile = dropbox_folder + file_list[counter].name
          message = "INFO: deleting file " + delfile + " from Dropbox\n"
          update_file (message, logfile)
          dbx.files_delete(delfile)
   
      counter += 1


def access_keepalive(verbose,keepalive_file,keepalive_action,tidy_list, logfile, keepalive_threshold=0):

    import os
    
    if keepalive_action == 'request':

        if os.path.isfile(keepalive_file):

            with open(keepalive_file, 'r') as f:
                lineList = f.readlines()
                if len(lineList) > 0:
                    lastLine = lineList[len(lineList)-1]
                    lastList = lastLine.split(":")
                    lastAction = lastList[0]
                    lastActionType = lastList[1]
                    lastActionSeq = lastList[2]
                    seq = int(lastActionSeq) + 1

                    if seq > keepalive_threshold:
                       tidy_flagfiles(tidy_list, logfile)
                       system_shutdown(logfile,restart=True)

                else:
                       seq = 0

        else:
            seq = 0

        datestr = get_date()
        message = "ACTION:request:" + str(seq) + ":"  + datestr  + "\n"
        update_file (message, keepalive_file)

    elif keepalive_action == 'respond':

        datestr = get_date()
        message = "ACTION:respond:0:" + datestr  + "\n"
        update_file (message, keepalive_file)

    else:
        pass


# decorator function
# parameter list (in order):
# trace_level = the level of debug information to be logged (0 = none)
# log_file = the filename (including path) to where log entries get written

def logging_decorator (trace_level,log_file):
    def real_decorator(f):

        from functools import wraps
        from datetime import datetime

        @wraps(f)
        def wrapped(*args, **kwargs):

            if trace_level > 0:
                datestr = get_date()
                update_file ("INFO: trace_level = %s, log entry made before function %s was called at: %s\n" % (str(trace_level),f.__name__,datestr),log_file)

            if trace_level > 1:
                t1 = datetime.now()

            r = f(*args, **kwargs)      # call the original function

            if trace_level > 1:
                t2 = datetime.now()
                elapsed_time = str((t2 - t1).total_seconds())
                update_file ("INFO: trace_level = %s, the time taken to execute function %s was %s seconds\n" % (str(trace_level),f.__name__,elapsed_time),log_file)

            if trace_level > 0:
                datestr = get_date()
                update_file ("INFO: trace_level = %s, log entry made after function %s was called at: %s\n" % (str(trace_level),f.__name__,datestr),log_file)

            return r
        return wrapped
    return real_decorator




