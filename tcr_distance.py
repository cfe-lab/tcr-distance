# Checked for Python 3.7

import sys, re, os, time, subprocess, shlex, shutil

sys.path.append( os.environ.get('BBLAB_UTIL_PATH', 'fail') )
import format_utils
import mailer

# todo: fix this path -> turn it into an env var
tcr_dist_path = os.environ.get('BBLAB_UTIL_PATH', 'fail') + "../apps/tcr-dist"
this_file_path = os.path.dirname(os.path.realpath(__file__))
tmp_dirs_path = this_file_path + "/tmp_dirs"

g_TIMEOUT = 600 * 3  # 30 mins


def create_random_directory():
	import random
	random.seed()
	
	os.chdir(tmp_dirs_path)	

	# find mostly unique dir_num	
	dir_num = str(random.randint(0, 100))
	while os.path.exists( "tmp_{}".format(dir_num) ):
		dir_num = dir_num + 1 #str(random.randint(0, 2**63 - 1))

	# make tmp_n folder to store intermediary files in. 
	tmpdir = "tmp_{}".format(dir_num)
	os.mkdir( tmpdir )
	os.chmod( tmpdir, 0o777 )

	return dir_num

# This function destroys a directory
def terminate(dir_num):
        assert (shutil.rmtree.avoids_symlink_attacks == True), "version needs to protect against symlink attacks"
        shutil.rmtree( "{}/tmp_{}".format(tmp_dirs_path, dir_num) )

# this function removes all files except for matricies.zip and status
def clear_dir(dir_num):
    #file = open("{}/status".format(wd), "a")
    #file.write("clearing directory! #{}".format(dir_num) + str("\n"))	   
    #file.close()	

    assert (shutil.rmtree.avoids_symlink_attacks == True), "version needs to protect against symlink attacks"
    for name in os.listdir( tmp_dirs_path + "/tmp_{}".format(dir_num) ):
        if name != "matricies.zip" and name != "status" and name != "terminate":
            file_path = "{}/tmp_{}/{}".format(tmp_dirs_path, dir_num, name)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree( file_path )

def debug_log_append(val):
        wd = tmp_dirs_path + "" # wd --> working directory
        file = open("{}/debug.log".format(wd), "a")
        file.write(str(val) + str("\n"))	   
        file.close()
	
# This function checks for any directories which are either empty or directories which hit an error and removes them.
def remove_bad_dirs():
    import datetime

    for name in os.listdir( tmp_dirs_path ):
        dir_path = tmp_dirs_path + "/" + name
        duration = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(dir_path)))
        hours_age = duration.days * 24 + (duration.seconds / 3600)
        if (os.path.isdir(dir_path) and len(os.listdir(dir_path)) == 0 and hours_age >= (1 / 60)) or \
           (os.path.exists(dir_path + "/terminate")) or \
           (hours_age > 48*2):
            # remove directory given that it should be destroyed or is empty and more than 1 minute old or more than 4 days old.
            assert (shutil.rmtree.avoids_symlink_attacks == True), "version needs to protect against symlink attacks"
            shutil.rmtree(dir_path)

def run(input_kind, filtered_contig_annotations, consensus_annotations, clones_file, dir_num, organism, send_email, email_address, download_file, forward_to_visualizer):

 
        ##### Check if directory exists.	


        os.chdir(tmp_dirs_path) 
        tmpdir = "tmp_{}".format(dir_num)
        if not os.path.exists( tmpdir ):
                return "directory not assigned"        
        wd = tmp_dirs_path + "/" + tmpdir # wd --> working directory


        ##### Convert annotations files into clones file (using tcr dist)
        
        def append_status_file(val):
                file = open("{}/status".format(wd), "a")
                file.write(str(val) + str("\n"))	   
                file.close()

        if input_kind == "10x":                
                append_status_file("starting 10x")
 
                # write input files to tmpdir 
                file = open("{}/filtered_contig_annotations.tsv".format(wd), "w")
                file.write(filtered_contig_annotations)
                file.close()

                file = open("{}/consensus_annotations.tsv".format(wd), "w")
                file.write(consensus_annotations)
                file.close()

                append_status_file("10x files written")

                command = "python2 {}/make_10x_clones_file.py -f {}/filtered_contig_annotations.tsv ".format(tcr_dist_path, wd) + \
                          "-c {}/consensus_annotations.tsv -o {}/clones_file --organism {}".format(wd, wd, organism)

                append_status_file("starting 10x conversion")
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      
                # This loop allows for the process to be terminated 
                process_done = False
                time_waited = 0
                while not process_done:
                        try: 
                                process.wait(1)  # give the process some time to complete.
                                process_done = True
                        except subprocess.TimeoutExpired as e:
                                time_waited += 1
                                if os.path.exists( tmpdir + "/terminate" ):
                                        process.terminate()
                                        append_status_file("took {} seconds".format(time_waited))
                                        append_status_file( "10x conversion terminated" )
                                        append_status_file( "done" )
                                        remove_bad_dirs()
                                        return
                                elif time_waited > g_TIMEOUT:
                                        process.terminate()
                                        append_status_file("took {} seconds".format(time_waited))
                                        append_status_file( "10x conversion timed out" )
                                        append_status_file( "done" )
                                        remove_bad_dirs()
                                        with open("{}/terminate".format(wd), "w") as f:
                                                f.write("terminate")
                                        return
 
                append_status_file("took {} seconds".format(time_waited))
                append_status_file("done 10x conversion")
                process.terminate()  # just in case

        elif input_kind == "clones_file":
                append_status_file("starting clones_file")

                # write input files to tmpdir 
                file = open("{}/clones_file".format(wd), "w")
                file.write(clones_file)
                file.close()

                append_status_file("clones_file written")


        ##### Convert clones file into matrix files (also using tcr dist)
        
        
        command = "python2 {}/compute_distances.py --clones_file {}/clones_file --organism {}".format(tcr_dist_path, wd, organism)

        append_status_file("starting distance computation");
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # This loop allows for the process to be terminated 
        process_done = False
        time_waited = 0
        while not process_done:
                try: 
                        process.wait(1)  # give the process some time to complete.
                        process_done = True
                except subprocess.TimeoutExpired as e:
                        time_waited += 1
                        if os.path.exists( tmpdir + "/terminate" ):
                                process.terminate()
                                append_status_file("took {} seconds".format(time_waited))
                                append_status_file( "distance computation terminated" )
                                append_status_file( "done" )
                                remove_bad_dirs()
                                return
                        elif time_waited > g_TIMEOUT:
                                process.terminate()
                                append_status_file("took {} seconds".format(time_waited))
                                append_status_file( "distance computation timed out" )
                                append_status_file( "done" )
                                remove_bad_dirs()
                                with open("{}/terminate".format(wd), "w") as f:
                                        f.write("terminate")
                                return

                        # TODO: do the errors before appending the error message so error check only has to check last line.
                        #website.send("Error Message: {}".format( str(e) ))
                        #stdout, stderr = process.communicate()
                        #website.send("Other errors: {}".format( stderr ))
 
        append_status_file("took {} seconds".format(time_waited))
        append_status_file("done distance computation")
        process.terminate()  # just in case


        ##### Compress 3 matrix files
       

        append_status_file("compressing files")

        command = "cd {}; zip matricies.zip clones__A.dist clones__B.dist clones__AB.dist; cd -".format(wd)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # This loop allows for the process to be terminated 
        process_done = False
        time_waited = 0
        while not process_done:
                try: 
                        process.wait(1)  # give the process some time to complete.
                        process_done = True
                except subprocess.TimeoutExpired as e:
                        time_waited += 1
                        if os.path.exists( tmpdir + "/terminate" ):
                                process.terminate()
                                append_status_file("took {} seconds".format(time_waited))
                                append_status_file( "compressing terminated" )
                                append_status_file( "done" )
                                remove_bad_dirs()
                                return
                        elif time_waited > g_TIMEOUT:
                                process.terminate()
                                append_status_file("took {} seconds".format(time_waited))
                                append_status_file( "compressing timed out" )
                                append_status_file( "done" )
                                remove_bad_dirs()
                                with open("{}/terminate".format(wd), "w") as f:
                                        f.write("terminate")
                                return
                        #website.send("Error Message: {}".format( str(e) ))
                        #stdout, stderr = process.communicate()
                        #website.send("Other errors: {}".format( stderr ))
 
        append_status_file("took {} seconds".format(time_waited))
        append_status_file("done compression")
        process.terminate()  # just in case

         
        ##### Very hacky check for any errors

       
        # If the output file doesn't exist, then destroy the current directory 
        if not os.path.exists("{}/matricies.zip".format(wd)):
                append_status_file("pipeline failed (output file was not generated). Make sure your input was correct.")
                append_status_file("done")
                time.sleep(5)
                terminate(dir_num)
                return

 
        ##### Read the compressed file and email it


        email_size = os.path.getsize("{}/matricies.zip".format(wd))
        if email_size * 1.37 < 25000000:    
                with open("{}/matricies.zip".format(wd), "rb") as file:
                        matricies_data = file.read()
                
 
        ##### Send an email with the xlsx file in it.


        # 1.37 is the factor around which files tend to be expanded.
        if send_email == 1 and email_size * 1.37 < 25000000:
                # make the output files into mailable files.
                mat_file = mailer.create_file( "matricies", 'zip', matricies_data )

                # Add the body to the message and send it.
                end_message = "This is an automatically generated email, please do not respond."
                msg_body = "The included .zip file ({}.zip) contains the requested tcr_distance matrix data. \n\n{}".format("matricies", end_message)

                if mailer.send_sfu_email("tcr_dist", email_address, "TCR Distance Results", msg_body, [mat_file]) == 0:
                        pass

                if not download_file:
                        append_status_file("no download") # in the case that only the email is sent, the directory is still terminated.
                        # can we also destroy everything during this step? 
        elif not download_file: # default to downloading the file
                append_status_file("request download")
                #clear_dir(dir_num)
        
        
        ##### Download file if selected


        if download_file: 
                append_status_file("request download")
                #clear_dir(dir_num)
         
        # This is only temporarily disabled       
        clear_dir(dir_num) # the idea here is that the directory is cleared when everything is done, but the zip is still there

        return
